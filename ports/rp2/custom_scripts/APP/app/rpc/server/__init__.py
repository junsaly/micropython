# app/rpc/server.py  RPC Server (USB CDC 串口传输)
# 对齐 STM32 版: RPCServer + dispatcher, 一行一个 JSON

import sys
import json

from app.rpc.protocols.jsonrpc import JSONRPCProtocol
from app.rpc.dispatch import RPCDispatcher


class RPCControl(object):
    '''rpc 控制实例: 通过 rpc.stop 停止服务并退出到 shell'''

    def __init__(self, server):
        self._server = server

    def stop(self):
        self._server.shut_down()
        return 'done'


class RPCServer(object):
    '''RPC Server: 从串口读一行 JSON 请求, 分发, 回一行 JSON'''

    def __init__(self, transport=None, protocol=None, dispatcher=None):
        self.transport = transport  # 预留: 可换 tcp/uart transport
        self.protocol = protocol or JSONRPCProtocol()
        self.dispatcher = dispatcher or RPCDispatcher()
        self.serving = False
        self._identity = 'pico'

    # ---------- 注册 ----------
    def register_instance(self, obj):
        '''注册驱动实例, 方法名变为 "实例名.方法名"'''
        self.dispatcher.register_instance(obj)

    def all_methods(self):
        return self.dispatcher.all_methods()

    # ---------- 主循环 ----------
    def run(self, stream_in=None, stream_out=None):
        stream_in = stream_in or sys.stdin
        stream_out = stream_out or sys.stdout
        self.serving = True
        print('{0} RPC server ready'.format(self._identity))
        while self.serving:
            line = stream_in.readline()
            if not line:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                request = self.protocol.parse_request(line.encode('utf8'))
                resp = self.dispatcher.dispatch(request)
                resp['version'] = 'MIX_2.0'
                stream_out.write(json.dumps(resp).encode('utf8') + b'\n')
            except Exception as e:
                resp = {'version': 'MIX_2.0', 'request_id': 0,
                        'error': {'code': -32700, 'message': str(e)}}
                stream_out.write(json.dumps(resp).encode('utf8') + b'\n')

    def shut_down(self):
        self.serving = False
