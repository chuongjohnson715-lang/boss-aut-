import ctypes
from ctypes import wintypes
from pathlib import Path

import win32gui
import win32ui
from PIL import Image

from core.edge_controller import EdgeController


BASE_DIR = Path(__file__).resolve().parent.parent
controller = EdgeController(BASE_DIR / "data")


print("=" * 50)
print("窗口区域诊断")
print("=" * 50)

if not controller.find_edge():
    print("Edge 查找失败")
    raise SystemExit
controller.activate()

hwnd = controller.hwnd
user32 = ctypes.windll.user32


print()
print("① 屏幕尺寸")
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
print(f"屏幕: {screen_w} x {screen_h}")


print()
print("② 工作区（排除任务栏）")
rect = wintypes.RECT()
user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
print(f"工作区: left={rect.left} top={rect.top} right={rect.right} bottom={rect.bottom}")
print(f"工作区尺寸: {rect.right - rect.left} x {rect.bottom - rect.top}")
print(f"任务栏高度: {screen_h - (rect.bottom - rect.top)}")


print()
print("③ GetWindowRect（窗口矩形）")
wr = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(wr))
print(f"窗口矩形: left={wr.left} top={wr.top} right={wr.right} bottom={wr.bottom}")
print(f"窗口尺寸: {wr.right - wr.left} x {wr.bottom - wr.top}")
print(f"超出屏幕右边: {wr.right - screen_w}  超出屏幕底边: {wr.bottom - screen_h}")


print()
print("④ GetClientRect（客户区）")
cr = wintypes.RECT()
user32.GetClientRect(hwnd, ctypes.byref(cr))
print(f"客户区: left={cr.left} top={cr.top} right={cr.right} bottom={cr.bottom}")
print(f"客户区尺寸: {cr.right - cr.left} x {cr.bottom - cr.top}")
print(f"标题栏+边框大约: {(wr.right - wr.left) - (cr.right - cr.left)} x {(wr.bottom - wr.top) - (cr.bottom - cr.top)}")


print()
print("⑤ ClientToScreen（客户区左上角屏幕坐标）")
pt = wintypes.POINT(0, 0)
user32.ClientToScreen(hwnd, ctypes.byref(pt))
print(f"客户区左上角屏幕坐标: ({pt.x}, {pt.y})")
print(f"客户区右下角屏幕坐标: ({pt.x + cr.right}, {pt.y + cr.bottom})")
print(f"客户区在屏幕内可见: 右下角 < ({screen_w}, {screen_h}) ? -> {pt.x + cr.right <= screen_w and pt.y + cr.bottom <= screen_h}")


print()
print("⑥ 窗口状态")
is_maximized = user32.IsZoomed(hwnd)
is_minimized = user32.IsIconic(hwnd)
print(f"最大化: {bool(is_maximized)}")
print(f"最小化: {bool(is_minimized)}")


print()
print("⑦ GetWindowDC 获取的 DC 尺寸")
hwnd_dc = win32gui.GetWindowDC(hwnd)
mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
# 获取 DC 的可见区域
clip = wintypes.RECT()
gdi32 = ctypes.windll.gdi32
gdi32.GetClipBox(mfc_dc.GetSafeHdc(), ctypes.byref(clip))
print(f"DC ClipBox: left={clip.left} top={clip.top} right={clip.right} bottom={clip.bottom}")
mfc_dc.DeleteDC()
win32gui.ReleaseDC(hwnd, hwnd_dc)


print()
print("=" * 50)
print("诊断结论")
print("=" * 50)
print()
print(f"屏幕: {screen_w} x {screen_h}")
print(f"窗口矩形: {wr.right - wr.left} x {wr.bottom - wr.top}")
print(f"客户区: {cr.right - cr.left} x {cr.bottom - cr.top}")
print(f"超出屏幕: 右边 {wr.right - screen_w}, 底边 {wr.bottom - screen_h}")
print()
print("经验法则: 截图应使用 客户区尺寸 或 工作区尺寸,")
print("而不是 GetWindowRect 的完整窗口矩形。")
print("因为最大化窗口的边框阴影延伸到了屏幕可视区域之外。")
