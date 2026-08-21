import ctypes
from pathlib import Path

import win32gui
import win32ui
from PIL import Image


class EdgeController:

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.hwnd = None
        self.title = None

    def find_edge(self):
        import ctypes
        import psutil

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        found_hwnds = []

        def enum_callback(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            try:
                proc = psutil.Process(pid.value)
                proc_name = proc.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return True

            title_length = user32.GetWindowTextLengthW(hwnd) + 1
            title_buf = ctypes.create_unicode_buffer(title_length)
            user32.GetWindowTextW(hwnd, title_buf, title_length)
            title = title_buf.value

            print(f"  HWND={hwnd}  PID={pid.value}  "
                  f"proc={proc_name}  visible=True  "
                  f"title={title[:40] if title else '(空)'}")

            if proc_name == "msedge.exe":
                found_hwnds.append(hwnd)

            return True

        enum_windows = user32.EnumWindows
        enum_windows.argtypes = [ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int), ctypes.c_int]
        enum_windows.restype = ctypes.c_bool

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(enum_callback)
        enum_windows(enum_proc, 0)

        if not found_hwnds:
            print("未找到任何 msedge.exe 窗口")
            return False

        self.hwnd = found_hwnds[0]

        title_length = user32.GetWindowTextLengthW(self.hwnd) + 1
        title_buf = ctypes.create_unicode_buffer(title_length)
        user32.GetWindowTextW(self.hwnd, title_buf, title_length)
        self.title = title_buf.value

        print(f"选用 Edge HWND={self.hwnd}  title={self.title}")
        return True

    def activate(self):
        if self.hwnd is None:
            return False

        if not win32gui.IsWindow(self.hwnd):
            return False

        if win32gui.IsIconic(self.hwnd):
            win32gui.ShowWindow(self.hwnd, 9)

        try:
            import ctypes
            import time

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            current_thread = kernel32.GetCurrentThreadId()

            target_thread = user32.GetWindowThreadProcessId(
                self.hwnd,
                None
            )

            attached = False

            if current_thread != target_thread:
                attached = user32.AttachThreadInput(
                    current_thread,
                    target_thread,
                    True
                )

            try:
                user32.BringWindowToTop(self.hwnd)
                user32.SetForegroundWindow(self.hwnd)
                user32.SetActiveWindow(self.hwnd)

            finally:
                if attached:
                    user32.AttachThreadInput(
                        current_thread,
                        target_thread,
                        False
                    )

            time.sleep(0.5)

            current_hwnd = win32gui.GetForegroundWindow()

            return current_hwnd == self.hwnd

        except Exception as e:
            print("激活 Edge 时发生异常：")
            print(repr(e))
            return False

    def get_rect(self):
        if self.hwnd is None:
            return None

        return win32gui.GetWindowRect(self.hwnd)

    def capture(self, filename="edge.png"):

        if self.hwnd is None:
            return False

        left, top, right, bottom = self.get_rect()

        width = right - left
        height = bottom - top

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()

        bitmap.CreateCompatibleBitmap(
            mfc_dc,
            width,
            height
        )

        save_dc.SelectObject(bitmap)

        user32 = ctypes.windll.user32

        result = user32.PrintWindow(
            self.hwnd,
            save_dc.GetSafeHdc(),
            2
        )

        if result != 1:
            return False

        bitmap_info = bitmap.GetInfo()

        bitmap_bits = bitmap.GetBitmapBits(True)

        image = Image.frombuffer(
            "RGB",
            (
                bitmap_info["bmWidth"],
                bitmap_info["bmHeight"]
            ),
            bitmap_bits,
            "raw",
            "BGRX",
            0,
            1
        )

        save_path = self.data_dir / filename

        image.save(save_path)

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(
            self.hwnd,
            hwnd_dc
        )

        return save_path

    def capture_dwm(self, filename="edge_dwm.png"):

        if self.hwnd is None:
            return False

        import ctypes
        from ctypes import wintypes

        dwm = ctypes.windll.dwmapi
        user32 = ctypes.windll.user32

        dwr = wintypes.RECT()
        dwm.DwmGetWindowAttribute(
            self.hwnd, 9,
            ctypes.byref(dwr), ctypes.sizeof(dwr)
        )
        dwm_w = dwr.right - dwr.left
        dwm_h = dwr.bottom - dwr.top

        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, dwm_w, dwm_h)
        save_dc.SelectObject(bitmap)

        result = user32.PrintWindow(
            self.hwnd,
            save_dc.GetSafeHdc(),
            2
        )

        if result != 1:
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwnd_dc)
            return False

        bitmap_info = bitmap.GetInfo()
        bitmap_bits = bitmap.GetBitmapBits(True)

        image = Image.frombuffer(
            "RGB",
            (bitmap_info["bmWidth"], bitmap_info["bmHeight"]),
            bitmap_bits,
            "raw", "BGRX", 0, 1
        )

        save_path = self.data_dir / filename
        image.save(save_path)

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, hwnd_dc)

        return save_path
