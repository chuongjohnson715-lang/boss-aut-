import ctypes

try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(
        ctypes.c_void_p(-4)
    )
except Exception:
    pass

from pathlib import Path
import win32gui
import win32ui
import win32con
from PIL import Image
import ctypes


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SCREENSHOT_PATH = DATA_DIR / "edge_window.png"


def capture_window(hwnd, save_path):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    print()
    print("窗口实际坐标：")
    print("left =", left)
    print("top =", top)
    print("right =", right)
    print("bottom =", bottom)
    
    width = right - left
    height = bottom - top
    
    print()
    print("截图尺寸：")
    print("width =", width)
    print("height =", height)

    width = right - left
    height = bottom - top

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    save_bitmap = win32ui.CreateBitmap()
    save_bitmap.CreateCompatibleBitmap(
        mfc_dc,
        width,
        height
    )

    save_dc.SelectObject(save_bitmap)

    user32 = ctypes.windll.user32

    result = user32.PrintWindow(
        hwnd,
        save_dc.GetSafeHdc(),
        2
    )

    if result != 1:
        print("窗口截图失败")
        return False
    bitmap_info = save_bitmap.GetInfo()
    bitmap_bits = save_bitmap.GetBitmapBits(True)

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

    image.save(save_path)

    win32gui.DeleteObject(save_bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return True


print("=" * 50)
print("Edge 窗口本体截图测试")
print("=" * 50)

edge_windows = []

def enum_callback(hwnd, _):
    if not win32gui.IsWindowVisible(hwnd):
        return

    title = win32gui.GetWindowText(hwnd)

    if "Microsoft" in title and "Edge" in title:
        edge_windows.append((hwnd, title))


win32gui.EnumWindows(enum_callback, None)

print()
print("检测到 Edge 窗口数量：", len(edge_windows))

if not edge_windows:
    print("没有找到 Edge")
else:
    hwnd, title = edge_windows[0]

    print()
    print("当前使用的 Edge：")
    print("HWND:", hwnd)
    print("标题:", title)

    print()
    print("正在截取 Edge 窗口本体...")

    success = capture_window(
        hwnd,
        SCREENSHOT_PATH
    )

    if success:
        print()
        print("截图成功")
        print("保存位置：")
        print(SCREENSHOT_PATH)

print()
print("=" * 50)
print("检测结束")
print("=" * 50)