# app/driver/ic/ad7175.py  AD7175 24-bit ADC 驱动
# 对齐 STM32 版 mix/driver/ic/ad7175.py 的 PLAD7175 API
# SPI 用 MicroPython machine.SPI (Pico 无 FT4222/PL 寄存器方案)

from machine import Pin, SPI
import time

__version__ = 'v0.1'


class AD717XDef:
    AD7175_CHIP_ID = 0x0DC2

    # 采样率配置表 (sps -> FILTER 寄存器值)
    SAMPLING_CONFIG_TABLE_AD7175 = {
        5: 0x14, 10: 0x13, 16.66: 0x12, 20: 0x11,
        49.96: 0x10, 59.92: 0x0f, 100: 0x0e, 200: 0x0d,
        397.5: 0x0c, 500: 0x0b, 1000: 0x0a, 2500: 0x09,
        5000: 0x08, 10000: 0x07, 15625: 0x06, 25000: 0x05,
        31250: 0x04, 50000: 0x03, 62500: 0x02, 125000: 0x01,
        250000: 0x00,
    }

    DEFAULT_TIMEOUT = 2.0

    # 寄存器地址
    COMM_REG_ADDR = 0x00
    STATUS_REG_ADDR = 0x00
    ADC_MODE_REG_ADDR = 0x01
    INTERFACE_MODE_REG_ADDR = 0x02
    REG_CHECK_REG_ADDR = 0x03
    DATA_REG_ADDR = 0x04
    GPIO_REG_ADDR = 0x06
    ID_REG_ADDR = 0x07
    CH0_MODE_REG_ADDR = 0x10
    CH1_MODE_REG_ADDR = 0x11
    CH2_MODE_REG_ADDR = 0x12
    CH3_MODE_REG_ADDR = 0x13

    CLOCKSEL_MASK = 0x0030

    CHANNELS = ['ch0', 'ch1', 'ch2', 'ch3', 'all', 0, 1, 2, 3]


class AD717XException(Exception):
    def __init__(self, err_str):
        self.err_str = err_str

    def __str__(self):
        return 'AD717XException: %s' % self.err_str


def CHAN(chan):
    if isinstance(chan, str):
        if chan in ('ch0', 'ch1', 'ch2', 'ch3'):
            return int(chan[-1])
        if chan == 'all':
            return 4
        raise AD717XException('channel %s error' % chan)
    if isinstance(chan, int):
        if chan in (0, 1, 2, 3):
            return chan
        if chan == 4:
            return 4
        raise AD717XException('channel %s error' % chan)
    raise AD717XException('channel %s error' % chan)


class PLAD7175(object):
    '''AD7175 ADC 驱动 (SPI 方式)'''

    rpc_public_api = ['reset', 'ic_init', 'read_volt', 'set_sampling_rate',
                      'get_sampling_rate', 'is_communication_ok']

    def __init__(self, spi_bus=None, mvref=5000, code_polar='bipolar',
                 reference='extern', buffer_flag='enable',
                 sck=None, mosi=None, miso=None, cs=None, freq=5000000):
        '''
        spi_bus: 可直接传 machine.SPI 实例; 不传则按 sck/mosi/miso 创建
        '''
        if spi_bus is not None:
            self.spi = spi_bus
        else:
            self.spi = SPI(0, baudrate=freq, polarity=0, phase=0,
                           sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.cs = Pin(cs, Pin.OUT) if cs is not None else None
        self.cs_high()
        self.mvref = mvref
        self.sample_rate_table = AD717XDef.SAMPLING_CONFIG_TABLE_AD7175
        self.resolution = 24
        self.channel_dict = {'ch0': 0, 'ch1': 1, 'ch2': 2, 'ch3': 3}
        self.config = {
            'ch0': {'P': 'AIN1', 'N': 'AIN0'},
            'ch1': {'P': 'AIN2', 'N': 'AIN3'},
        }
        self.sampling_rates = {}

    # ---------- SPI 底层 ----------
    def cs_high(self):
        if self.cs is not None:
            self.cs.value(1)

    def cs_low(self):
        if self.cs is not None:
            self.cs.value(0)

    def _transfer(self, tx):
        self.cs_low()
        try:
            return self.spi.read(len(tx), tx)
        finally:
            self.cs_high()

    # ---------- 寄存器操作 ----------
    def read_register(self, reg_addr, length=1):
        tx = bytearray([0x40 | reg_addr] + [0x00] * length)
        data = self._transfer(bytes(tx))
        if length == 1:
            return data[1]
        return data[1:]

    def write_register(self, reg_addr, reg_data):
        if isinstance(reg_data, int):
            if reg_data > 0xFF:
                tx = bytearray([0x00 | reg_addr,
                                (reg_data >> 8) & 0xFF, reg_data & 0xFF])
            else:
                tx = bytearray([0x00 | reg_addr, reg_data & 0xFF])
        else:
            tx = bytearray([0x00 | reg_addr] + list(reg_data))
        self._transfer(bytes(tx))

    # ---------- 公共 API ----------
    def ic_init(self):
        self.reset()
        return 'done'

    def reset(self):
        # AD7175 需要至少 64 个 DIN=1 周期触发复位
        self.cs_low()
        try:
            self.spi.write(bytes([0xFF]) * 8)
        finally:
            self.cs_high()
        time.sleep_ms(10)
        return 'done'

    def _value_2_mvolt(self, code, mvref, bits):
        # 双极性: 满量程 = mvref
        return (code - (1 << (bits - 1))) * mvref / (1 << (bits - 1))

    def read_volt(self, channel, timeout_sec=AD717XDef.DEFAULT_TIMEOUT):
        if channel not in AD717XDef.CHANNELS:
            raise AD717XException('channel %s error' % channel)
        ch = CHAN(channel)
        # 选择单通道 (简化: 用 CH 模式寄存器)
        self.write_register(AD717XDef.CH0_MODE_REG_ADDR + ch, 0x00)
        time.sleep_ms(50)  # 等待转换
        reg_data = self.read_register(AD717XDef.DATA_REG_ADDR, 3)
        code = (reg_data[0] << 16) | (reg_data[1] << 8) | reg_data[2]
        return round(self._value_2_mvolt(code, self.mvref, self.resolution), 6)

    def set_sampling_rate(self, channel, rate):
        if rate not in self.sample_rate_table:
            raise AD717XException('sampling rate %s not supported' % rate)
        ch = CHAN(channel)
        self.write_register(AD717XDef.CH0_MODE_REG_ADDR + ch,
                            self.sample_rate_table[rate])
        self.sampling_rates[channel] = rate
        return 'done'

    def get_sampling_rate(self, channel):
        return self.sampling_rates.get(channel, 5)

    def is_communication_ok(self):
        try:
            reg_data = self.read_register(AD717XDef.ID_REG_ADDR, 2)
            chip_id = (reg_data[0] << 8) | reg_data[1]
            return chip_id == AD717XDef.AD7175_CHIP_ID
        except Exception:
            return False
