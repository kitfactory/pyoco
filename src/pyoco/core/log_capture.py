import contextlib
import io
import threading
import sys
from typing import Dict, Iterator, List, Optional, TextIO, Tuple


class _ThreadCaptureStream:
    def __init__(self, original: TextIO):
        self.original = original
        self._lock = threading.RLock()
        self._buffers: Dict[int, List[io.StringIO]] = {}

    def write(self, data: str) -> int:
        with self._lock:
            self.original.write(data)
            buffers = self._buffers.get(threading.get_ident())
            if buffers:
                buffers[-1].write(data)
        return len(data)

    def flush(self):
        with self._lock:
            self.original.flush()

    @contextlib.contextmanager
    def capture(self):
        thread_id = threading.get_ident()
        buffer = io.StringIO()
        with self._lock:
            self._buffers.setdefault(thread_id, []).append(buffer)
        try:
            yield buffer
        finally:
            with self._lock:
                stack = self._buffers.get(thread_id)
                if stack:
                    stack.pop()
                    if not stack:
                        self._buffers.pop(thread_id, None)

    def __getattr__(self, name: str):
        return getattr(self.original, name)


class RunLogCapture:
    def __init__(self, stdout: Optional[TextIO] = None, stderr: Optional[TextIO] = None):
        self._stdout_proxy = _ThreadCaptureStream(stdout or sys.stdout)
        self._stderr_proxy = _ThreadCaptureStream(stderr or sys.stderr)

    @contextlib.contextmanager
    def activate(self):
        with contextlib.redirect_stdout(self._stdout_proxy), contextlib.redirect_stderr(self._stderr_proxy):
            yield self

    @contextlib.contextmanager
    def capture_task(self) -> Iterator[Tuple[io.StringIO, io.StringIO]]:
        with self._stdout_proxy.capture() as stdout_buf, self._stderr_proxy.capture() as stderr_buf:
            yield stdout_buf, stderr_buf
