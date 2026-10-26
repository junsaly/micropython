# Pico2 入口：启动 MIX RPC Server (USB CDC 串口)
# 协议: MIX_2.0 JSON-RPC, 一行一个请求, 换行分隔

import sys

sys.path.insert(0, '/APP')

from rpc.server.server import RPCServer
from rpc.services.picoservice import PicoService

# DMM 服务：无硬件时用 mock ADC 验证 RPC 链路
try:
    from rpc.services.dmm.dmm import DMMService
    dmm_ok = True
except Exception:
    dmm_ok = False


class MockAD7175(object):
    '''无硬件时模拟 AD7175，用于验证 RPC 调用链路'''
    def reset(self):
        pass

    def read_volt(self, channel, timeout_sec=2):
        return round(1234.567, 3)

    def set_sampling_rate(self, channel, rate):
        self._rate = rate

    def get_sampling_rate(self, channel):
        return getattr(self, '_rate', 5000)

    def set_channel_state(self, channel, state):
        pass

    def select_single_channel(self, channel):
        pass

    def is_communication_ok(self):
        return True

    def config_max_value_measure(self, channel, samples):
        pass

    def enable_continuous_sampling(self, channel, rate, samples=1):
        pass

    def disable_continuous_sampling(self, channel):
        pass

    def get_continuous_sampling_voltage(self, channel, count):
        return [1234.567] * count


def main():
    server = RPCServer(identity='pico')
    server.register('pico', PicoService())

    if dmm_ok:
        server.register('dmm', DMMService(adc=MockAD7175()))
        print('DMM service registered (mock mode)')
    else:
        print('DMM service load failed')

    server.run()


main()
