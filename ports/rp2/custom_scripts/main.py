import sys
import json

# ============================================================
#  Pico2 RPC Server over USB CDC
#  Wire: newline-delimited JSON, one request per line
#  Request:  {"version":"MIX_2.0","id":1,"remote_id":"pico","method":"ping","args":[],"kwargs":{}}
#  Response: {"version":"MIX_2.0","request_id":1,"result":"pong"}
#  Error:    {"version":"MIX_2.0","request_id":1,"error":{"code":-32601,"message":"unknown method"}}
# ============================================================

def rpc_ping(args, kwargs):
    return "pong"

def rpc_add(args, kwargs):
    a = args[0] if len(args) > 0 else kwargs.get("a", 0)
    b = args[1] if len(args) > 1 else kwargs.get("b", 0)
    return a + b

def rpc_hello(args, kwargs):
    name = args[0] if len(args) > 0 else "world"
    return "Hello, " + name + "!"

# 注册方法表
methods = {
    "ping":  rpc_ping,
    "add":   rpc_add,
    "hello": rpc_hello,
}

def handle_request(line):
    try:
        req = json.loads(line)
    except:
        return None

    rid = req.get("id", 0)
    method = req.get("method", "")
    args = req.get("args", [])
    kwargs = req.get("kwargs", {})

    if method not in methods:
        resp = {
            "version": "MIX_2.0",
            "request_id": rid,
            "error": {"code": -32601, "message": "unknown method: " + method}
        }
    else:
        try:
            result = methods[method](args, kwargs)
            resp = {
                "version": "MIX_2.0",
                "request_id": rid,
                "result": result
            }
        except Exception as e:
            resp = {
                "version": "MIX_2.0",
                "request_id": rid,
                "error": {"code": -32603, "message": str(e)}
            }

    return json.dumps(resp) + "\n"

print("Pico2 RPC server ready")

while True:
    line = sys.stdin.readline()
    if not line:
        continue
    line = line.strip()
    if not line:
        continue
    resp = handle_request(line)
    if resp:
        sys.stdout.write(resp)
