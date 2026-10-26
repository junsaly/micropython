# DMM 数字万用表服务 (RPC Service)
# 参考 mix/driver/smartgiant/common/ic/ad717x.py 的 AD7175 API
# 说明: 这里是协议层封装, SPI 总线部分在 Pico 上要用 machine.SPI 实现
#       (原框架的 FT4222/FTSPI 是 USB-Host 方案, Pico 上不存在)

import json


class DMMService(object):
    '''DMM 数字万用表服务, 基于 AD7175 24-bit ADC'''

    rpc_public_api = [
        'get_id', 'reset', 'read_volt', 'read_volts',
        'set_sampling_rate', 'get_sampling_rate',
        'set_channel_state', 'select_single_channel',
        'is_communication_ok', 'config_max_value_measure',
        'enable_continuous_sampling', 'disable_continuous_sampling',
        'get_continuous_sampling_voltage',
    ]

    CHANNELS = ['ch0', 'ch1', 'ch2', 'ch3']

    def __init__(self, adc=None):
        '''
        adc: AD7175 实例。在 Pico 上通过 machine.SPI 创建:
             from machine import SPI, Pin
             spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
                       sck=Pin(2), mosi=Pin(3), miso=Pin(4))
             adc = AD7175(spi, mvref=5000, cs=Pin(5))
        '''
        self._adc = adc
        self._info = {
            'module': 'DMM',
            'adc': 'AD7175',
            'resolution': 24,
        }

    # ---------- 内部工具 ----------
    def _require_adc(self):
        if self._adc is None:
            raise RuntimeError('AD7175 not initialized')

    # ---------- RPC 公共 API ----------
    def get_id(self):
        self._require_adc()
        return self._info

    def reset(self):
        self._require_adc()
        self._adc.reset()
        return 'ok'

    def read_volt(self, channel='ch0', timeout_sec=2):
        self._require_adc()
        return self._adc.read_volt(channel, timeout_sec)

    def read_volts(self, channels=None):
        '''读多个通道, 返回 dict {ch0: mv, ch1: mv}'''
        self._require_adc()
        if channels is None:
            channels = self.CHANNELS
        result = {}
        for ch in channels:
            result[ch] = self._adc.read_volt(ch)
        return result

    def set_sampling_rate(self, channel, rate):
        self._require_adc()
        self._adc.set_sampling_rate(channel, rate)
        return 'ok'

    def get_sampling_rate(self, channel):
        self._require_adc()
        return self._adc.get_sampling_rate(channel)

    def set_channel_state(self, channel, state):
        self._require_adc()
        self._adc.set_channel_state(channel, state)
        return 'ok'

    def select_single_channel(self, channel):
        self._require_adc()
        self._adc.select_single_channel(channel)
        return 'ok'

    def is_communication_ok(self):
        self._require_adc()
        return self._adc.is_communication_ok()

    def config_max_value_measure(self, channel, samples):
        self._require_adc()
        self._adc.config_max_value_measure(channel, samples)
        return 'ok'

    def enable_continuous_sampling(self, channel, rate, samples=1):
        self._require_adc()
        self._adc.enable_continuous_sampling(channel, rate, samples)
        return 'ok'

    def disable_continuous_sampling(self, channel):
        self._require_adc()
        self._adc.disable_continuous_sampling(channel)
        return 'ok'

    def get_continuous_sampling_voltage(self, channel, count):
        self._require_adc()
        return self._adc.get_continuous_sampling_voltage(channel, count)
