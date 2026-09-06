"""Bounded qtest transport for authored graphics fixtures."""
import select
import time

class VerificationError(RuntimeError):
    pass


def check(condition, message):
    if not condition:
        raise VerificationError(message)


class QTest:
    def __init__(self, process, timeout):
        self.process = process
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        self.buffer = b""
        self.commands = 0

    def command(self, command):
        self.process.stdin.write((command + "\n").encode("ascii"))
        self.process.stdin.flush()
        deadline = self.deadline
        self.commands += 1
        while True:
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([self.process.stdout], [], [], max(0, remaining))[0]:
                    raise VerificationError("qtest response timed out: " + command[:100])
                chunk = self.process.stdout.read1(65536)
                if not chunk:
                    raise VerificationError("QEMU closed qtest: " + command[:100])
                self.buffer += chunk
            line, self.buffer = self.buffer.split(b"\n", 1)
            response = line.decode("ascii").strip()
            if response.startswith("IRQ "):
                continue
            check(response == "OK" or response.startswith("OK "), "qtest: " + response)
            return response[2:].strip()

    def read(self, address, size):
        suffix = {1: "b", 2: "w", 4: "l", 8: "q"}[size]
        return int(self.command(f"read{suffix} {address:#x}"), 0)

    def write(self, address, value, size):
        suffix = {1: "b", 2: "w", 4: "l", 8: "q"}[size]
        self.command(f"write{suffix} {address:#x} {value:#x}")

    def memory_write(self, address, data):
        self.command(f"write {address:#x} {len(data)} 0x{data.hex()}")

    def memory_read(self, address, size):
        value = self.command(f"read {address:#x} {size}")
        return bytes.fromhex(value.removeprefix("0x"))

