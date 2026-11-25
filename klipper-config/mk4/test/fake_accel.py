# Solo para pruebas en batch: imita la interfaz de adxl345_i2c sin I2C.
# Incluye batch_bulk (streaming simulado) y falla si alguien reprograma el
# chip mientras emite datos (lo que haría el homing sin suspender BoostKit).
import logging
from . import bulk_sensor

REG_THRESH_ACT = 0x24


class FakeAccel:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.axes_map = [(0, -1.), (1, 1.), (2, -1.)]
        self.regs = {}
        self.streaming = False
        self.batch_bulk = bulk_sensor.BatchBulkHelper(
            self.printer, self._batch, self._start, self._finish, 0.1)
        self.printer.lookup_object('gcode').register_command(
            '_BK_STATUS', self.cmd_BK_STATUS)

    def cmd_BK_STATUS(self, gcmd):
        # En batch las respuestas no van al log: se escribe a mano.
        bk = self.printer.lookup_object('boostkit')
        reactor = self.printer.get_reactor()
        reactor.pause(reactor.monotonic() + gcmd.get_float('WAIT', 0.))
        now = reactor.monotonic()
        bk.next_time = 0.
        logging.info("BK %s", bk.get_status(now))

    def set_reg(self, reg, val, minclock=0):
        if self.streaming and reg == REG_THRESH_ACT:
            raise self.printer.command_error(
                "fake_accel: chip reprogrammed while streaming")
        self.regs[reg] = val

    def read_reg(self, reg):
        return self.regs.get(reg, 0)

    def _start(self):
        self.streaming = True
        logging.info("fake_accel: stream start")

    def _finish(self):
        self.streaming = False
        logging.info("fake_accel: stream stop")

    def _batch(self, eventtime):
        if not self.streaming:
            return {}
        t = self.printer.lookup_object('mcu').estimated_print_time(eventtime)
        return {'data': [(t - 0.01 * i, 120. + i, -80., 9790. + i % 3)
                         for i in range(10, 0, -1)]}


def load_config_prefix(config):
    return FakeAccel(config)
