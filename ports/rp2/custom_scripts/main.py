# Pico2 入口: 读 confighw_profile.json 装配驱动并启动 RPC Server
# 协议: MIX_2.0 JSON-RPC, USB CDC 串口, 一行一个请求

import sys
import json

# APP 目录挂到 sys.path, 使 "import app.rpc.server" 可用
sys.path.insert(0, '/APP')

from app.rpc.server import RPCServer
from app.driver.ic.ad7175 import PLAD7175
from app.driver.module.dmm import PRM_DMM, MockAD7175


# ---------- 配置装配 (对齐 STM32 launcher 思路) ----------

def create_shared_devices(profile):
    '''创建 shared_devices 中的实例, 支持 @引用'''
    devices = {}
    shared = profile.get('shared_devices', {})
    for name, cfg in shared.items():
        obj = None
        cls = cfg.get('class')
        if cls == 'PLAD7175':
            if cfg.get('mock', False):
                obj = MockAD7175()
            else:
                obj = PLAD7175(
                    sck=cfg.get('sck'), mosi=cfg.get('mosi'),
                    miso=cfg.get('miso'), cs=cfg.get('cs'),
                    freq=cfg.get('freq', 5000000),
                    mvref=cfg.get('mvref', 5000))
        devices[name] = obj
    return devices


def resolve_ref(value, devices):
    '''@xxx 引用解析'''
    if isinstance(value, str) and value.startswith('@'):
        return devices.get(value[1:])
    return value


def create_dut_instances(profile, devices):
    '''创建 dut 实例 dict, 返回 {实例名: 对象}'''
    objs = {}
    for dut in profile.get('duts', {}).values():
        for name, cfg in dut.items():
            if not isinstance(cfg, dict) or 'class' not in cfg:
                continue
            cls = cfg['class']
            if cls == 'PRM_DMM':
                adc = resolve_ref(cfg.get('ad7175'), devices)
                objs[name] = PRM_DMM(ad7175=adc)
    return objs


# ---------- 主流程 ----------

def main():
    # 读配置
    try:
        with open('/APP/app/confighw_profile.json', 'r') as f:
            profile = json.load(f)
    except Exception as e:
        print('config load failed: {0}'.format(e))
        profile = {}

    # 装配
    shared = create_shared_devices(profile)
    dut_objs = create_dut_instances(profile, shared)

    # 启动 RPC Server 并注册实例 (方法名: "dmm.measure")
    server = RPCServer()
    server.register_instance(dut_objs)

    print('registered methods: {0}'.format(json.dumps(server.all_methods())))
    server.run()


main()
