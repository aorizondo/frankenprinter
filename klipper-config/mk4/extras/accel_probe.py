# EXPERIMENTAL: Z probe by nozzle tap, detected with the ADXL345 on the head
#
# The bed rises until it touches the nozzle; the knock reaches the head and
# the ADXL345 activity interrupt (chip Z axis, AC coupled) raises INT1. INT1 is
# the same GPIO endstop that [accel_endstop] uses for X/Y crash homing, so this
# probe shares that MCU endstop (a pin can only be declared once). It replaces
# [probe]: both cannot be loaded at the same time.
#
# Needs [accel_endstop] (extras/accel_endstop.py) and the accelerometer it
# points to. Install by symlinking into ~/klipper/klippy/extras/.
#
#   [accel_probe]
#   z_offset: 0.0             # nozzle is the probe: calibrate with PROBE_CALIBRATE
#   threshold: 0.5            # g on the chip Z axis (ACCEL_NOISE_TEST AXIS=Z)
#   #blank_time: 0.15         # s after the move starts before arming INT1
#   #settle_time: 0.3         # s of dwell before each probe (XY ringing)
#   #z_current: 0.8           # A on _vref_z while probing (less force if missed)
#   speed: 3.0                # usual [probe] options: speed, lift_speed,
#   samples: 3                # samples, sample_retract_dist, samples_result,
#   ...                       # samples_tolerance, samples_tolerance_retries
#
# Works with PROBE, PROBE_ACCURACY, PROBE_CALIBRATE, BED_MESH_CALIBRATE and
# Z homing through probe:z_virtual_endstop. x_offset/y_offset default to 0.
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import logging
from . import probe

# MCU_endstop view of the shared INT1 endstop that only exposes the Z
# steppers (homing checks "triggered prior to movement" on every stepper it
# is given; X/Y do not move while probing) and arms the chip at move start.
class _TapEndstop:
    def __init__(self, accel_endstop, blank_time):
        self.ae = accel_endstop
        self.mcu_endstop = accel_endstop.mcu_endstop
        self.blank_time = blank_time
        self.z_steppers = []
    def get_mcu(self):
        return self.mcu_endstop.get_mcu()
    def add_stepper(self, stepper):
        # The shared endstop must stop Z too; X/Y were added by accel_endstop
        self.mcu_endstop.add_stepper(stepper)
        self.z_steppers.append(stepper)
    def get_steppers(self):
        return list(self.z_steppers)
    def home_start(self, print_time, sample_time, sample_count, rest_time,
                   triggered=True):
        self.ae._schedule_enable(print_time, self.blank_time)
        return self.mcu_endstop.home_start(print_time, sample_time,
                                           sample_count, rest_time,
                                           triggered=triggered)
    def home_wait(self, home_end_time):
        return self.mcu_endstop.home_wait(home_end_time)
    def query_endstop(self, print_time):
        return self.mcu_endstop.query_endstop(print_time)

# mcu_probe for PrinterProbe-like objects (same interface as
# probe.ProbeEndstopWrapper)
class _TapProbeSession:
    def __init__(self, config, accel_endstop, probe_offsets, param_helper):
        self.printer = config.get_printer()
        self.ae = accel_endstop
        self.threshold = config.getfloat('threshold', 0.5, minval=0.0625,
                                         maxval=15.9)
        self.settle_time = config.getfloat('settle_time', 0.3, minval=0.,
                                           maxval=2.)
        self.z_current = config.getfloat('z_current', None, above=0.,
                                         maxval=1.5)
        blank_time = config.getfloat('blank_time', 0.15, minval=0., maxval=1.)
        self.tap_endstop = _TapEndstop(accel_endstop, blank_time)
        self.query_endstop = self.tap_endstop.query_endstop
        self.homing_helper = probe.DescendToEndstopHelper(
            config, self.tap_endstop, probe_offsets, param_helper)
        self.saved_z_current = None
    def _set_z_current(self, amps):
        gcode = self.printer.lookup_object('gcode')
        gcode.run_script_from_command("SET_PIN PIN=_vref_z VALUE=%.3f"
                                      % (amps,))
    def start_probe_session(self, gcmd):
        self.homing_helper.clear_trigger_positions()
        if self.z_current is not None and self.saved_z_current is None:
            obj = self.printer.lookup_object('output_pin _vref_z')
            scale = self.printer.lookup_object('configfile').get_status(
                None)['settings']['output_pin _vref_z'].get('scale', 1.)
            now = self.printer.get_reactor().monotonic()
            self.saved_z_current = obj.get_status(now)['value'] * scale
            self._set_z_current(self.z_current)
        return self
    def run_probe(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        if self.settle_time:
            toolhead.dwell(self.settle_time)
        toolhead.wait_moves()
        threshold = gcmd.get_float('TAP_THRESHOLD', self.threshold,
                                   minval=0.0625, maxval=15.9)
        self.ae._prepare(2, threshold)
        try:
            self.homing_helper.descend_until_trigger(gcmd)
        finally:
            self.ae._disarm()
    def pull_probed_results(self):
        return self.homing_helper.pull_trigger_positions()
    def end_probe_session(self):
        self.homing_helper.clear_trigger_positions()
        if self.saved_z_current is not None:
            amps = self.saved_z_current
            self.saved_z_current = None
            self._set_z_current(amps)

class AccelProbe:
    def __init__(self, config):
        self.printer = config.get_printer()
        accel_endstop = self.printer.load_object(config, 'accel_endstop')
        self.probe_offsets = probe.ProbeOffsetsHelper(config)
        self.param_helper = probe.ProbeParameterHelper(config)
        self.mcu_probe = _TapProbeSession(config, accel_endstop,
                                          self.probe_offsets,
                                          self.param_helper)
        self.probe_session = probe.SampleAveragingHelper(
            config, self.param_helper, self.mcu_probe.start_probe_session)
        query_endstop = self.mcu_probe.query_endstop
        self.cmd_helper = probe.ProbeCommandHelper(config, self, query_endstop)
        probe.HomingViaProbeHelper(config, self.probe_offsets.get_offsets()[2],
                                   query_endstop)
        self.printer.add_object('probe', self)
        logging.info("accel_probe: nozzle tap probe on %s",
                     accel_endstop.chip_name)
    def get_probe_params(self, gcmd=None):
        return self.param_helper.get_probe_params(gcmd)
    def get_offsets(self, gcmd=None):
        return self.probe_offsets.get_offsets(gcmd)
    def get_status(self, eventtime):
        return self.cmd_helper.get_status(eventtime)
    def start_probe_session(self, gcmd):
        return self.probe_session.start_probe_session(gcmd)

def load_config(config):
    return AccelProbe(config)
