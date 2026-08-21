from pathlib import Path
import ctypes
from ctypes import wintypes
import win32gui
import win32ui
from PIL import Image

from core.edge_controller import EdgeController

BASE_DIR = Path(__file__).resolve().parent.parent
controller = EdgeController(BASE_DIR / "data")

print("=" * 55)
print("DWM 完整截图测试")
print("=" * 55)

if not controller.find_edge():
    print("Edge 查找失败")
    raise SystemExit
controller.activate()
hwnd = controller.hwnd

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
SRCCOPY = 0x00CC0020

# ====== 获取各区域 ======
print()
print("① 各区域坐标")

screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
print(f"  屏幕: {screen_w} x {screen_h}")

wr = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(wr))
print(f"  GetWindowRect: ({wr.left},{wr.top})-({wr.right},{wr.bottom})  = {wr.right-wr.left}x{wr.bottom-wr.top}")

cr = wintypes.RECT()
user32.GetClientRect(hwnd, ctypes.byref(cr))
pt = wintypes.POINT(0, 0)
user32.ClientToScreen(hwnd, ctypes.byref(pt))
print(f"  客户区 ClientToScreen: ({pt.x},{pt.y}) 尺寸: {cr.right}x{cr.bottom}")

dwr = wintypes.RECT()
dwm = ctypes.windll.dwmapi
dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(dwr), ctypes.sizeof(dwr))
dwm_w = dwr.right - dwr.left
dwm_h = dwr.bottom - dwr.top
print(f"  DwmFrameBounds: ({dwr.left},{dwr.top})-({dwr.right},{dwr.bottom})  = {dwm_w}x{dwm_h}")


print()
print("② 方法 A: 从桌面 DC 截取 DWM 区域")

# 桌面 DC 从 (dwr.left, dwr.top) 截取 dwm_w x dwm_h
screen_dc = win32gui.GetDC(0)
mfc_dc = win32ui.CreateDCFromHandle(screen_dc)
mem_dc = mfc_dc.CreateCompatibleDC()
bmp = win32ui.CreateBitmap()
bmp.CreateCompatibleBitmap(mfc_dc, dwm_w, dwm_h)
mem_dc.SelectObject(bmp)
ok = gdi32.BitBlt(mem_dc.GetSafeHdc(), 0, 0, dwm_w, dwm_h,
                  mfc_dc.GetSafeHdc(), dwr.left, dwr.top, SRCCOPY)
print(f"  BitBlt 结果: {'成功' if ok else '失败'}")
bits = bmp.GetBitmapBits(True)
img = Image.frombuffer("RGB", (dwm_w, dwm_h), bits, "raw", "BGRX", 0, 1)
img.save(BASE_DIR / "data" / "fix_dwm_桌面DC.png")
print(f"  保存: data/fix_dwm_桌面DC.png  ({dwm_w}x{dwm_h})")
mem_dc.DeleteDC()
mfc_dc.DeleteDC()
win32gui.ReleaseDC(0, screen_dc)
win32gui.DeleteObject(bmp.GetHandle())


print()
print("③ 方法 B: 从窗口 DC 截取 DWM 尺寸")

# 用 GetWindowDC 获取窗口 DC, 然后 BitBlt 从 (0,0) 截取 dwm_w x dwm_h
hwnd_dc = win32gui.GetWindowDC(hwnd)
mfc2 = win32ui.CreateDCFromHandle(hwnd_dc)
mem2 = mfc2.CreateCompatibleDC()
bmp2 = win32ui.CreateBitmap()
bmp2.CreateCompatibleBitmap(mfc2, dwm_w, dwm_h)
mem2.SelectObject(bmp2)
ok2 = gdi32.BitBlt(mem2.GetSafeHdc(), 0, 0, dwm_w, dwm_h,
                   mfc2.GetSafeHdc(), 0, 0, SRCCOPY)
print(f"  BitBlt 结果: {'成功' if ok2 else '失败'}")
bits2 = bmp2.GetBitmapBits(True)
img2 = Image.frombuffer("RGB", (dwm_w, dwm_h), bits2, "raw", "BGRX", 0, 1)
img2.save(BASE_DIR / "data" / "fix_dwm_窗口DC.png")
print(f"  保存: data/fix_dwm_窗口DC.png  ({dwm_w}x{dwm_h})")
mem2.DeleteDC()
mfc2.DeleteDC()
win32gui.ReleaseDC(hwnd, hwnd_dc)
win32gui.DeleteObject(bmp2.GetHandle())


print()
print("④ 方法 C: 直接 PrintWindow 用 DWM 尺寸")

cr2 = wintypes.RECT()
user32.GetClientRect(hwnd, ctypes.byref(cr2))
dc3 = win32gui.GetWindowDC(hwnd)
mfc3 = win32ui.CreateDCFromHandle(dc3)
mem3 = mfc3.CreateCompatibleDC()
bmp3 = win32ui.CreateBitmap()
bmp3.CreateCompatibleBitmap(mfc3, dwm_w, dwm_h)
mem3.SelectObject(bmp3)
user32.PrintWindow(hwnd, mem3.GetSafeHdc(), 2)  # PW_RENDERFULLCONTENT
bits3 = bmp3.GetBitmapBits(True)
img3 = Image.frombuffer("RGB", (dwm_w, dwm_h), bits3, "raw", "BGRX", 0, 1)
img3.save(BASE_DIR / "data" / "fix_dwm_PrintWindow.png")
print(f"  保存: data/fix_dwm_PrintWindow.png  ({dwm_w}x{dwm_h})")
mem3.DeleteDC()
mfc3.DeleteDC()
win32gui.ReleaseDC(hwnd, dc3)
win32gui.DeleteObject(bmp3.GetHandle())


print()
print("=" * 55)
print("请对比 data/ 下的 3 张新截图:")
print("  fix_dwm_桌面DC.png     ← 从桌面 DC 截取 DWM 区域")
print("  fix_dwm_窗口DC.png     ← 从窗口 DC 截取 DWM 区域")
print("  fix_dwm_PrintWindow.png ← PrintWindow 用 DWM 尺寸")
print("告诉我哪张是完整的？")
print("=" * 55)
