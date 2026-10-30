# app/cli.py  串口字符指令层 (Shell)
# 位置: RPC 服务之上。上电默认 RPC; RPC 内调 rpc.stop 退出到本层;
#      本层输入 run rpc 回到 RPC; 任意层 Ctrl+C 退出到 MicroPython REPL。
# 特性: 逐字符回显、退格、Tab 补全(指令/参数)、回车执行。

import sys
import machine


class Shell(object):
    PROMPT = 'pico> '

    # 补全树: 前缀匹配, 叶节点为完整指令/参数
    COMPLETE_TREE = {
        'help': {},
        'run': {'rpc': {}},
        'set': {'io': {'high': {}, 'low': {}}},
        'get': {'io': {}},
        'eval': {},
        'reboot': {},
    }

    def __init__(self, context=None, on_run_rpc=None):
        self._ctx = context or {}      # eval 时可见的符号表
        self._on_run_rpc = on_run_rpc  # run rpc 回调(重新进入 RPC 循环)
        self._line = ''

    # ---------- 指令实现 ----------
    def _cmd_help(self, args):
        return ('Pico2 shell commands:\r\n'
                '  help                    show this help\r\n'
                '  run rpc                 start RPC server (JSON-RPC on this port)\r\n'
                '  set io <pin> high|low   set GPIO output level\r\n'
                '  get io <pin>            read GPIO input level\r\n'
                '  eval <expr>             evaluate python expression, e.g. eval 1+1\r\n'
                '  reboot                  soft reset\r\n'
                'Tab completes commands/args. Ctrl+C exits to MicroPython REPL.')

    def _cmd_run(self, args):
        if args and args[0] == 'rpc':
            return None  # None -> 退出 shell, 回到 RPC
        return 'usage: run rpc'

    def _cmd_set(self, args):
        if len(args) >= 3 and args[0] == 'io':
            try:
                pin = int(args[1])
                level = 1 if args[2] == 'high' else 0
            except ValueError:
                return 'usage: set io <pin> high|low'
            if not 0 <= pin <= 28:
                return 'pin out of range (0-28)'
            p = machine.Pin(pin, machine.Pin.OUT)
            p.value(level)
            return 'io %d -> %s' % (pin, 'high' if level else 'low')
        return 'usage: set io <pin> high|low'

    def _cmd_get(self, args):
        if len(args) >= 2 and args[0] == 'io':
            try:
                pin = int(args[1])
            except ValueError:
                return 'usage: get io <pin>'
            if not 0 <= pin <= 28:
                return 'pin out of range (0-28)'
            p = machine.Pin(pin, machine.Pin.IN)
            return 'io %d = %s' % (pin, 'high' if p.value() else 'low')
        return 'usage: get io <pin>'

    def _cmd_eval(self, args):
        expr = ' '.join(args)
        if not expr:
            return 'usage: eval <expr>'
        try:
            return repr(eval(expr, self._ctx))
        except Exception as e:
            return 'eval error: %r' % e

    def _cmd_reboot(self, args):
        machine.reset()

    COMMANDS = {
        'help': _cmd_help,
        'run': _cmd_run,
        'set': _cmd_set,
        'get': _cmd_get,
        'eval': _cmd_eval,
        'reboot': _cmd_reboot,
    }

    # ---------- 执行 ----------
    def _execute(self, cmd):
        parts = cmd.split(' ')
        name = parts[0]
        args = [p for p in parts[1:] if p]
        fn = self.COMMANDS.get(name)
        if fn is None:
            sys.stdout.write('unknown command: %s (type help)\r\n' % cmd)
            return
        try:
            result = fn(self, args)
        except Exception as e:
            sys.stdout.write('error: %r\r\n' % e)
            return
        if result is None:
            return 'exit'  # run rpc: 结束 shell
        if result:
            sys.stdout.write(str(result) + '\r\n')

    # ---------- 补全 ----------
    def _complete(self):
        tokens = self._line.split(' ')
        cur = tokens[-1] if tokens else ''
        node = Shell.COMPLETE_TREE
        for t in tokens[:-1]:
            if not t:
                continue
            nxt = node.get(t)
            if nxt is None:
                sys.stdout.write('\x07')  # 中间 token 无法匹配
                return
            node = nxt
        cands = [k for k in node if k.startswith(cur)]
        if len(cands) == 1:
            rest = cands[0][len(cur):]
            self._line += rest
            sys.stdout.write(rest)
        elif len(cands) > 1:
            sys.stdout.write('\r\n')
            for k in sorted(cands):
                sys.stdout.write(k + '  ')
            sys.stdout.write('\r\n' + Shell.PROMPT + self._line)
        else:
            sys.stdout.write('\x07')

    # ---------- 主循环 ----------
    def _prompt(self):
        sys.stdout.write(Shell.PROMPT)

    def run(self):
        sys.stdout.write('\r\nPico2 shell (help for commands, Ctrl+C to REPL)\r\n')
        self._prompt()
        while True:
            c = sys.stdin.read(1)
            if not c:
                continue
            o = ord(c)
            if o == 3:            # Ctrl+C -> REPL
                raise KeyboardInterrupt
            elif o == 4:          # Ctrl+D ignore
                continue
            elif o == 13 or o == 10:   # CR / LF -> execute
                sys.stdout.write('\r\n')
                cmd = self._line.strip()
                self._line = ''
                if cmd and self._execute(cmd) == 'exit':
                    return
                self._prompt()
            elif o == 8 or o == 127:   # backspace
                if self._line:
                    self._line = self._line[:-1]
                    sys.stdout.write('\b \b')
            elif o == 9:          # Tab -> complete
                self._complete()
            elif 32 <= o <= 126:
                self._line += c
                sys.stdout.write(c)
