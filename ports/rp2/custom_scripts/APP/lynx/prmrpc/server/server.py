# MicroPython RPC 精简版 server
# 参考 mix/rpc/server/server.py + requesthandler.py
# 传输层：USB CDC 串口，一行一个 JSON（换行分隔）

import sys
import json

from rpc.protocols.jsonrpc import JSONRPCProtocol, JSONRPCResponse


class RequestHandlerMixin(object):
    '''处理单个 RPC 请求，调用 service 上的方法'''

    def call_method(self, request, service):
        if hasattr(service, 'rpc_public_property'):
            if request.method[:8] == '__fget__':
                if request.method[8:] in service.rpc_public_property:
                    return getattr(service, request.method[8:])
            if request.method[:8] == '__fset__':
                if request.method[8:] in service.rpc_public_property:
                    return setattr(service, request.method[8:], request.args[0])

        if request.method not in service.rpc_public_api:
            raise AttributeError(
                '{0} is not a public function on {1}'.format(
                    request.method, service.__class__.__name__))

        method = getattr(service, request.method)
        if not hasattr(request, 'args'):
            if not hasattr(request, 'kwargs'):
                result = method()
            else:
                result = method(**request.kwargs)
        else:
            if not hasattr(request, 'kwargs'):
                result = method(*request.args)
            else:
                result = method(*request.args, **request.kwargs)
        return result

    def handle_request(self, request, service):
        try:
            result = self.call_method(request, service)
            return JSONRPCResponse(request.id, result)
        except Exception as e:
            return JSONRPCResponse(request.id, result=None,
                                   error_code=-32603, error_msg=str(e))


class RPCServer(RequestHandlerMixin):
    '''精简版 RPC Server：串口一行一个 JSON 请求'''

    rpc_public_api = ['version', 'identity', 'get_service_info',
                      'get_all_services', 'get_all_registered_services']

    def __init__(self, identity='pico', protocol=None, stream_in=None, stream_out=None):
        self._identity = identity
        self.protocol = protocol or JSONRPCProtocol()
        self.stream_in = stream_in or sys.stdin
        self.stream_out = stream_out or sys.stdout
        self.services = {}
        self.serving = False
        self._version = '1.0.0'
        self._up_since = 0

    # ========== 服务注册 ==========
    def register(self, name, service):
        if not hasattr(service, 'rpc_public_api'):
            raise ValueError(
                '{0} has no rpc_public_api'.format(type(service).__name__))
        self.services[name] = service

    def get_service(self, name):
        return self.services.get(name)

    # ========== 主循环 ==========
    def run(self):
        self.serving = True
        print('{0} RPC server ready'.format(self._identity))
        self._up_since = __import__('time').ticks_ms()
        while self.serving:
            line = self.stream_in.readline()
            if not line:
                continue
            line = line.strip()
            if not line:
                continue
            try:
                request = self.protocol.parse_request(line.encode('utf8'))
                # remote_id 即服务名；'__server__' 是服务器自身
                if request.remote_id == '__server__':
                    service = self
                else:
                    service = self.services.get(request.remote_id)
                if service is None:
                    resp = self.protocol.error_response(
                        request.id, -32601,
                        'service not found: {0}'.format(request.remote_id))
                else:
                    resp = self.handle_request(request, service)
                self.stream_out.write(resp.serialize() + b'\n')
            except Exception as e:
                try:
                    import json as _j
                    resp = {'version': 'MIX_2.0',
                            'request_id': 0,
                            'error': {'code': -32700, 'message': str(e)}}
                    self.stream_out.write(_j.dumps(resp).encode('utf8') + b'\n')
                except Exception:
                    pass

    def shut_down(self):
        self.serving = False

    # ========== 内置公共 API ==========
    def version(self):
        return self._version

    def identity(self):
        return self._identity

    def get_service_info(self, service_name):
        s = self.services.get(service_name)
        if s is None:
            return None
        return {'name': service_name,
                'public_api': list(s.rpc_public_api)}

    def get_all_services(self):
        return tuple(name for name in self.services.keys()
                     if not name.startswith('__'))

    def get_all_registered_services(self):
        return tuple(self.services.keys())
