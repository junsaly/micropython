# Pico2 入口：启动 MIX RPC Server (USB CDC 串口)
# 协议: MIX_2.0 JSON-RPC, 一行一个请求, 换行分隔

import sys

sys.path.insert(0, '/APP')

from rpc.server.server import RPCServer
from rpc.services.picoservice import PicoService


def main():
    server = RPCServer(identity='pico')
    server.register('pico', PicoService())
    server.run()


main()
