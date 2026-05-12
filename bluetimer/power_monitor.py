from __future__ import annotations

import sys
import threading
from collections.abc import Callable


class PowerMonitor:
    def __init__(self, on_resume: Callable[[], None]) -> None:
        self.on_resume = on_resume
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        if sys.platform == "win32":
            self._thread.start()

    def _run(self) -> None:
        try:
            import win32con
            import win32gui
        except Exception:
            return

        class_name = "BlueTimerPowerWatcher"

        def wnd_proc(hwnd, msg, wparam, lparam):
            pbt_apmresumeautomatic = 0x0012
            if msg == win32con.WM_POWERBROADCAST and wparam == pbt_apmresumeautomatic:
                self.on_resume()
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

        wc = win32gui.WNDCLASS()
        wc.lpszClassName = class_name
        wc.lpfnWndProc = wnd_proc
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass
        win32gui.CreateWindow(class_name, "", 0, 0, 0, 0, 0, 0, 0, None, None)
        win32gui.PumpMessages()
