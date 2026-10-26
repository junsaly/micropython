# MicroPython 精简版 MIX RPC 协议层
# 与 mix/rpc/protocols/jsonrpc.py 保持协议兼容 (MIX_2.0)

import json
import time


class JSONRPCError(RuntimeError):
    def __init__(self, request_id, error_dict):
        self.request_id = request_id
        self.code = error_dict['code']
        self.msg = error_dict['message']

    def __str__(self):
        return 'RPC error({0}: {1}'.format(self.code, self.msg)


class JSONRPCResponse(object):
    def __init__(self, request_id, result=None, error_code=0, error_msg=None):
        self.version = JSONRPCProtocol.version
        self.request_id = request_id
        if error_code != 0:
            self.error = {'code': error_code, 'message': error_msg}
        else:
            self.result = result

    def dump_json(self):
        d = {'version': self.version, 'request_id': self.request_id}
        if hasattr(self, 'error'):
            d['error'] = self.error
        else:
            d['result'] = self.result
        return json.dumps(d)

    def serialize(self):
        return self.dump_json().encode('utf8')


class JSONRPCRequest(object):
    def __init__(self, remote_id, method, args=None, kwargs=None):
        self.version = JSONRPCProtocol.version
        self.id = time.ticks_us()
        self.remote_id = remote_id
        self.method = method
        if args:
            if isinstance(args, str):
                args = [args]
            self.args = args
        if kwargs and len(kwargs) > 0:
            self.kwargs = kwargs

    def dump_json(self):
        d = {'version': self.version, 'id': self.id,
             'remote_id': self.remote_id, 'method': self.method}
        if hasattr(self, 'args'):
            d['args'] = self.args
        if hasattr(self, 'kwargs'):
            d['kwargs'] = self.kwargs
        return json.dumps(d)

    def serialize(self):
        return self.dump_json().encode('utf8')


class JSONRPCProtocol(object):
    version = 'MIX_2.0'

    def create_request(self, remote_id, method, args, kwargs):
        return JSONRPCRequest(remote_id, method, args, kwargs)

    def create_response(self, request_id, result):
        return JSONRPCResponse(request_id, result)

    def error_response(self, request_id, error_code, error_msg):
        return JSONRPCResponse(request_id, result=None,
                               error_code=error_code, error_msg=error_msg)

    def parse_response(self, data):
        d = json.loads(data.decode('utf8'))
        if 'error' in d:
            raise JSONRPCError(d['request_id'], d['error'])
        return JSONRPCResponse(d['request_id'], d['result'])

    def parse_request(self, data):
        d = json.loads(data.decode('utf8'))
        request = JSONRPCRequest(d['remote_id'], d['method'],
                                 d.get('args', []), d.get('kwargs', {}))
        request.id = d['id']
        return request
