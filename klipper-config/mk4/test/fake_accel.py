# Solo para pruebas en batch: imita la interfaz de adxl345_i2c sin I2C
class FakeAccel:
    def __init__(self, config):
        self.axes_map = [(0, -1.), (1, 1.), (2, -1.)]
        self.regs = {}
    def set_reg(self, reg, val, minclock=0):
        self.regs[reg] = val
    def read_reg(self, reg):
        return self.regs.get(reg, 0)
def load_config_prefix(config):
    return FakeAccel(config)
