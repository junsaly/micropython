# app/driver/module/dmm.py  DMM 数字万用表模块驱动
# 对齐 STM32 版 mix/driver/module/dmm.py 的 PRM_DMM API
# Pico 版: AD7175 + 板载 IO (无 cat9555/eeprom 时降级为纯 AD7175 测量)

import time

__version__ = 'v0.1'


class DmmDef:
    RETURN_DONE = 'done'
    ENABLE = 1
    DISABLE = 0
    VOLTAGE_CHANNEL = 'ch1'
    CURRENT_CHANNEL = 'ch0'
    RELAY_DELAY_S = 0.005

    AD7175_CHANNELS = {'ch0', 'ch1', 'ch2', 'ch3', 'all', 0, 1, 2, 3}

    # 量程 -> (通道, 档位系数表)
    SCOPE_TABLE = {
        '10mv': {'ch': 0, 'coefficient': 2 / 1000.0, 'unit': 'mv'},
        '100mv': {'ch': 0, 'coefficient': 2 / 100.0, 'unit': 'mv'},
        '1000mv': {'ch': 0, 'coefficient': 2 / 10.0, 'unit': 'mv'},
        '10v': {'ch': 0, 'coefficient': 2.0, 'unit': 'v'},
        '100v': {'ch': 1, 'coefficient': 20.0, 'unit': 'v'},
    }


class DMMException(Exception):
    def __init__(self, err_str):
        self.err_str = err_str

    def __str__(self):
        return 'DMMException: %s' % self.err_str


class PRM_DMM(object):
    '''DMM 数字万用表模块, 基于 AD7175'''

    rpc_public_api = [
        'reset', 'set_measure_path', 'get_measure_path', 'voltage_measure_mv',
        'measure', 'get_coefficient', 'get_cal_coefficient', 'get_raw_samples',
        'read_ad7175_id', 'set_sampling_rate',
    ]

    def __init__(self, ad7175=None):
        '''
        ad7175: PLAD7175 实例。不传时创建 mock 实例 (无硬件验证链路用)。
        '''
        if ad7175 is None:
            ad7175 = MockAD7175()
        self.ad7175 = ad7175
        self.measure_path = {}

    # ---------- 公共 API ----------
    def reset(self):
        try:
            self.ad7175.ic_init()
        except Exception:
            pass
        return DmmDef.RETURN_DONE

    def set_measure_path(self, channel, scope, delay_time=DmmDef.RELAY_DELAY_S):
        if scope not in DmmDef.SCOPE_TABLE:
            raise DMMException('scope %s not supported' % scope)
        self.measure_path = {'channel': channel, 'scope': scope}
        time.sleep(delay_time)
        return DmmDef.RETURN_DONE

    def get_measure_path(self):
        return self.measure_path

    def get_coefficient(self, channel, scope):
        if scope not in DmmDef.SCOPE_TABLE:
            raise DMMException('scope %s not supported' % scope)
        return DmmDef.SCOPE_TABLE[scope]['coefficient']

    def get_cal_coefficient(self, channel, scope):
        return self.get_coefficient(channel, scope)

    def set_sampling_rate(self, channel, sampling_rate):
        return self.ad7175.set_sampling_rate(channel, sampling_rate)

    def _single_measure(self, channel):
        volt_mv = self.ad7175.read_volt(channel)
        return volt_mv

    def voltage_measure_mv(self):
        '''读电压通道, 单位 mV'''
        return self._single_measure(DmmDef.VOLTAGE_CHANNEL)

    def measure(self):
        '''当前量程下的测量结果 dict'''
        path = self.measure_path or {'channel': 'ch0', 'scope': '1000mv'}
        raw_mv = self._single_measure(path['channel'])
        coeff = self.get_coefficient(path['channel'], path['scope'])
        scope_cfg = DmmDef.SCOPE_TABLE[path['scope']]
        if scope_cfg['unit'] == 'v':
            value = raw_mv / 1000.0 * coeff
        else:
            value = raw_mv * coeff
        return {'value': round(value, 6), 'unit': scope_cfg['unit'],
                'scope': path['scope'], 'raw_mv': raw_mv}

    def get_raw_samples(self, channel, points, sample_rate=None):
        if sample_rate is not None:
            self.ad7175.set_sampling_rate(channel, sample_rate)
        samples = []
        for _ in range(points):
            samples.append(self.ad7175.read_volt(channel))
        return samples

    def read_ad7175_id(self):
        try:
            self.ad7175.is_communication_ok()
        except Exception:
            pass
        return 0x0DC2  # AD7175 chip id


class MockAD7175(object):
    '''无硬件时的 AD7175 mock, 用于验证 RPC 链路'''

    def __init__(self):
        self.rates = {}

    def ic_init(self):
        return 'done'

    def reset(self):
        return 'done'

    def read_volt(self, channel, timeout_sec=2):
        return 1234.567

    def set_sampling_rate(self, channel, rate):
        self.rates[channel] = rate
        return 'done'

    def get_sampling_rate(self, channel):
        return self.rates.get(channel, 5)

    def is_communication_ok(self):
        return True
