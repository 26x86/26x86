"""Run an offline helper with bounded memory and a wall-clock deadline.

Both pipes are drained without blocking: POSIX nonblocking reads and Windows
PeekNamedPipe ensure a quiet stream cannot stall a busy stream. No background
reader threads survive a timeout or an inherited pipe held by another process.
"""

from __future__ import annotations

import math
import os
import subprocess
import time


class BoundedProcessError(subprocess.SubprocessError):
    """An execution limit or pipe failure, retaining bounded diagnostic bytes."""

    def __init__(self, reason, command, *, timeout, returncode, stdout, stderr,
                 elapsed, detail=None):
        self.reason = reason
        self.cmd = command
        self.timeout = timeout
        self.returncode = returncode
        self.stdout = self.output = stdout
        self.stderr = stderr
        self.elapsed = elapsed
        message = f"Helper failed: {reason} after {elapsed:.3f}s"
        if detail:
            message += ": " + detail
        super().__init__(message)


if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    import msvcrt

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _peek_pipe = _kernel32.PeekNamedPipe
    _peek_pipe.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
                          ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
                          ctypes.POINTER(wintypes.DWORD)]
    _peek_pipe.restype = wintypes.BOOL


def _read_ready(pipe, amount):
    """Return available bytes, b'' for EOF, or None if no bytes are ready."""
    descriptor = pipe.fileno()
    if os.name == "nt":
        available = wintypes.DWORD()
        handle = msvcrt.get_osfhandle(descriptor)
        if not _peek_pipe(handle, None, 0, None, ctypes.byref(available), None):
            error = ctypes.get_last_error()
            if error in (109, 232, 233):  # broken/no-data/disconnected pipe
                return b""
            raise ctypes.WinError(error)
        if not available.value:
            return None
        return os.read(descriptor, min(amount, available.value))
    try:
        return os.read(descriptor, amount)
    except BlockingIOError:
        return None


def run_bounded(command, *, timeout=30, stdout_limit=4 * 1024 * 1024,
                stderr_limit=64 * 1024):
    """Return CompletedProcess with bytes; nonzero exit codes remain inspectable.

    ``stdout_limit`` and ``stderr_limit`` count bytes, and a stream exactly at
    its limit is valid. An extra byte, timeout, or pipe failure raises
    BoundedProcessError after killing/reaping the spawned child. Its stdout and
    stderr retain at most the requested limits. stdin is always DEVNULL.
    """
    if isinstance(command, (str, bytes)):
        raise ValueError("command must be an argument sequence, never a shell string")
    command = list(command)
    if not command:
        raise ValueError("command cannot be empty")
    if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError("timeout must be finite and positive")
    for name, limit in (("stdout_limit", stdout_limit), ("stderr_limit", stderr_limit)):
        if type(limit) is not int or limit < 0:
            raise ValueError(name + " must be a nonnegative integer")

    started = time.monotonic()
    deadline = started + timeout
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, shell=False)
    streams = [("stdout", process.stdout, stdout_limit, bytearray()),
               ("stderr", process.stderr, stderr_limit, bytearray())]
    reason = detail = None
    cleanup_deadline = None

    def kill_child():
        if process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass

    try:
        if os.name != "nt":
            for _, pipe, _, _ in streams:
                os.set_blocking(pipe.fileno(), False)
        while True:
            now = time.monotonic()
            if reason is None and now >= deadline:
                reason = "timeout"
            if reason is not None and cleanup_deadline is None:
                kill_child()
                cleanup_deadline = now + 1.0
            progress = False
            for name, pipe, limit, captured in streams:
                if pipe.closed:
                    continue
                try:
                    chunk = _read_ready(pipe, min(65536, limit - len(captured) + 1))
                except OSError as exc:
                    if reason is None:
                        reason, detail = "pipe-read-error", str(exc)
                    pipe.close()
                    continue
                if chunk is None:
                    continue
                progress = True
                if not chunk:
                    pipe.close()
                    continue
                remaining = limit - len(captured)
                captured.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    if reason is None:
                        reason = name + "-limit"
                    # This stream is full. Retaining or draining additional
                    # bytes cannot improve bounded diagnostics.
                    pipe.close()
            returncode = process.poll()
            if returncode is not None and all(pipe.closed for _, pipe, _, _ in streams):
                break
            if cleanup_deadline is not None and time.monotonic() >= cleanup_deadline:
                break
            if not progress:
                until = cleanup_deadline if cleanup_deadline is not None else deadline
                time.sleep(max(0, min(0.01, until - time.monotonic())))
        if reason is not None:
            kill_child()
        returncode = process.wait(timeout=1)
    except BaseException:
        kill_child()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        raise
    finally:
        for _, pipe, _, _ in streams:
            pipe.close()
    stdout, stderr = (bytes(item[3]) for item in streams)
    if reason is not None:
        raise BoundedProcessError(reason, command, timeout=timeout, returncode=returncode,
            stdout=stdout, stderr=stderr, elapsed=time.monotonic() - started, detail=detail)
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr=stderr)
