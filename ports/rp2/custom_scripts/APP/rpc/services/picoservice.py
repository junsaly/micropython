# 示例服务：Pico 板卡控制
# 参考 mix/rpc/services 的写法：service 必须带 rpc_public_api

import json


class PicoService(object):
    '''Pico 板卡服务'''

    rpc_public_api = ['ping', 'echo', 'get_temperature', 'set_led', 'get_info']

    def __init__(self):
        self._info = {
            'board': 'Raspberry Pi Pico',
            'serial': 'Pico2',
            'firmware': 'MicroPython',
        }

    def ping(self):
        return 'pong'

    def echo(self, msg):
        return msg

    def get_temperature(self):
        # RP2040 内部温度传感器（近似）
        import machine
        adc = machine.ADC(4)
        voltage = adc.read_u16() * 3.3 / 65535
        temp = 27 - (voltage - 0.706) / 0.001721
        return round(temp, 2)

    def set_led(self, state):
        from machine import Pin
        led = Pin(25, Pin.OUT)
        led.value(1 if state else 0)
        return 'ok' if state else 'off'

    def get_info(self):
        return self._info
