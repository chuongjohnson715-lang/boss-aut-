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

                current_thread = user32.GetCurrentThreadId()

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

    def activate(self):
        if self.hwnd is None:
            return False

        if not win32gui.IsWindow(self.hwnd):
            return False

        if win32gui.IsIconic(self.hwnd):
            win32gui.ShowWindow(self.hwnd, 9)

        try:
            import ctypes

            user32 = ctypes.windll.user32

            current_thread = user32.GetCurrentThreadId()

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

            import time
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