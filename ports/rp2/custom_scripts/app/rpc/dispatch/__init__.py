# app/rpc/dispatch.py  RPC 分发器
# 对齐 STM32 版 mix/lynx/prmrpc/dispatch/__init__.py 的行为:
#   - register_instance({'dmm': dmm_obj}) 注册实例
#   - 方法名路由: "dmm.measure" (实例名.方法名)
#   - 支持 rpc_public_api 白名单

import json

NAME_METHOD_SEPARATOR = '.'


class RPCError(Exception):
    pass


class JSONRPCMethodNotFoundError(RPCError):
    pass


class RPCDispatcher(object):
    '''方法分发器: 维护 实例名 -> {方法名: 函数} 的映射'''

    def __init__(self):
        self.method_map = {}          # 无前缀方法
        self.subdispatchers = {}      # {prefix: [dispatcher, ...]}

    def add_method(self, f, name=None):
        if not name:
            name = f.__name__
        if name in self.method_map:
            raise RPCError('Name %s already registered' % name)
        self.method_map[name] = f

    def register_instance(self, obj):
        '''注册实例, obj 可以是 dict {'name': instance} 或单个实例'''
        if not isinstance(obj, dict):
            obj = {'': obj}
        for prefix, instance in obj.items():
            dispatch = self.__class__()
            for name, f in self.get_public(instance).items():
                dispatch.add_method(f, name)
            if prefix:
                prefix += NAME_METHOD_SEPARATOR
            self.subdispatchers.setdefault(prefix, []).append(dispatch)

    def get_public(self, obj):
        '''获取实例的 rpc_public_api 方法映射 {方法名: 函数}'''
        rpc = {}
        if hasattr(obj, 'rpc_public_api'):
            for k in obj.rpc_public_api:
                attr = getattr(obj, k, None)
                if attr is None:
                    raise RPCError(
                        'rpc_public_api entry "{0}" not found on {1}'.format(
                            k, obj.__class__.__name__))
                rpc[k] = attr
            return rpc
        # 无 rpc_public_api 时, 暴露所有非下划线开头方法
        for name in dir(obj):
            if name.startswith('_'):
                continue
            attr = getattr(obj, name)
            if callable(attr):
                rpc[name] = attr
        return rpc

    def get_method(self, name):
        '''按名字找方法: 先查无前缀, 再查 前缀.方法名'''
        if name in self.method_map:
            return self.method_map[name]
        for prefix, subdispatchers in self.subdispatchers.items():
            if prefix and name.startswith(prefix):
                method_name = name[len(prefix):]
                for sd in subdispatchers:
                    try:
                        return sd.get_method(method_name)
                    except JSONRPCMethodNotFoundError:
                        pass
        raise JSONRPCMethodNotFoundError('Method not found: ' + name)

    def dispatch(self, request):
        '''分发一个请求, 返回响应 (dict 形式, 由 server 负责序列化)'''
        try:
            method = self.get_method(request.method)
            if hasattr(request, 'args'):
                if hasattr(request, 'kwargs'):
                    result = method(*request.args, **request.kwargs)
                else:
                    result = method(*request.args)
            else:
                if hasattr(request, 'kwargs'):
                    result = method(**request.kwargs)
                else:
                    result = method()
            return {'request_id': request.id, 'result': result}
        except JSONRPCMethodNotFoundError as e:
            return {'request_id': request.id,
                    'error': {'code': -32601, 'message': str(e)}}
        except Exception as e:
            return {'request_id': request.id,
                    'error': {'code': -32603, 'message': str(e)}}

    def all_methods(self):
        '''返回所有已注册方法 {prefix: [methods]}'''
        ret = {'': list(self.method_map.keys())}
        for prefix, sds in self.subdispatchers.items():
            ret[prefix] = []
            for sd in sds:
                ret[prefix] += list(sd.method_map.keys())
        return ret
