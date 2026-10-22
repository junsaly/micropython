import sys

print("Pico2 raw mode")

while True:
    ch = sys.stdin.read(1)
    if ch:
        sys.stdout.write(ch)
