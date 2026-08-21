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
print("全面截图诊断")
print("=" * 55)

if not controller.find_edge():
    print("Edge 查找失败")
    raise SystemExit
controller.activate()
hwnd = controller.hwnd

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
SRCCOPY = 0x00CC0020

# ====== 屏幕信息 ======
print()
print("① 屏幕信息")
screen_w = user32.GetSystemMetrics(0)
screen_h = user32.GetSystemMetrics(1)
print(f"  GetSystemMetrics: {screen_w} x {screen_h}")

# 物理屏幕尺寸（通过 EnumDisplaySettings）
class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmPosition", wintypes.POINT),
        ("dmDisplayOrientation", ctypes.c_ulong),
        ("dmDisplayFixedOutput", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_long),
        ("dmPelsHeight", ctypes.c_long),
        ("dmBitsPerPel", ctypes.c_ulong),
        # ... 剩余字段不重要
    ]

for i in range(2):
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    ret = user32.EnumDisplaySettingsW(None, i, ctypes.byref(dm))
    if ret:
        print(f"  EnumDisplaySettings mode {i}: {dm.dmPelsWidth} x {dm.dmPelsHeight}")

# DPI
dc = win32gui.GetDC(0)
dpi_x = gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
dpi_y = gdi32.GetDeviceCaps(dc, 90)  # LOGPIXELSY
win32gui.ReleaseDC(0, dc)
print(f"  DPI: {dpi_x} x {dpi_y}  (标准 96 = 100%)")
print(f"  实际缩放: {dpi_x / 96 * 100:.0f}%")

# ====== 窗口信息 ======
print()
print("② 窗口信息")
wr = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(wr))
print(f"  GetWindowRect: {wr.right-wr.left} x {wr.bottom-wr.top}")

cr = wintypes.RECT()
user32.GetClientRect(hwnd, ctypes.byref(cr))
print(f"  GetClientRect: {cr.right-cr.left} x {cr.bottom-cr.top}")

# DwmGetWindowAttribute 获取真实目标大小
DWM_EXTENDED_FRAME_BOUNDS = 9
dwm = ctypes.windll.dwmapi
dwr = wintypes.RECT()
dwm.DwmGetWindowAttribute(
    hwnd, DWM_EXTENDED_FRAME_BOUNDS,
    ctypes.byref(dwr), ctypes.sizeof(dwr)
)
print(f"  DwmExtFrameBounds: {dwr.right-dwr.left} x {dwr.bottom-dwr.top}")

# 窗口是否最大化
print(f"  IsZoomed(最大化): {bool(user32.IsZoomed(hwnd))}")

# ====== 截取全屏 ======
print()
print("③ 截取全屏")
screen_dc = win32gui.GetDC(0)
screen_mfc = win32ui.CreateDCFromHandle(screen_dc)
screen_mem = screen_mfc.CreateCompatibleDC()
full_bmp = win32ui.CreateBitmap()
full_bmp.CreateCompatibleBitmap(screen_mfc, screen_w, screen_h)
screen_mem.SelectObject(full_bmp)
gdi32.BitBlt(screen_mem.GetSafeHdc(), 0, 0, screen_w, screen_h,
             screen_mfc.GetSafeHdc(), 0, 0, SRCCOPY)
full_bits = full_bmp.GetBitmapBits(True)
full_img = Image.frombuffer("RGB", (screen_w, screen_h), full_bits, "raw", "BGRX", 0, 1)
full_img.save(BASE_DIR / "data" / "diagnose_全屏.png")
print(f"  全屏截图: {screen_w} x {screen_h}  -> data/diagnose_全屏.png")

screen_mem.DeleteDC()
screen_mfc.DeleteDC()
win32gui.ReleaseDC(0, screen_dc)
win32gui.DeleteObject(full_bmp.GetHandle())

# ====== 截取 Dwm 区域 ======
print()
print("④ 截取 DwmFrameBounds")
dwm_w = dwr.right - dwr.left
dwm_h = dwr.bottom - dwr.top
screen_dc2 = win32gui.GetDC(0)
mfc2 = win32ui.CreateDCFromHandle(screen_dc2)
mem2 = mfc2.CreateCompatibleDC()
bmp2 = win32ui.CreateBitmap()
bmp2.CreateCompatibleBitmap(mfc2, dwm_w, dwm_h)
mem2.SelectObject(bmp2)
gdi32.BitBlt(mem2.GetSafeHdc(), 0, 0, dwm_w, dwm_h,
             mfc2.GetSafeHdc(), dwr.left, dwr.top, SRCCOPY)
bits2 = bmp2.GetBitmapBits(True)
img2 = Image.frombuffer("RGB", (dwm_w, dwm_h), bits2, "raw", "BGRX", 0, 1)
img2.save(BASE_DIR / "data" / "diagnose_Dwm区域.png")
print(f"  DwmFrameBounds截图: {dwm_w} x {dwm_h}  -> data/diagnose_Dwm区域.png")

mem2.DeleteDC()
mfc2.DeleteDC()
win32gui.ReleaseDC(0, screen_dc2)
win32gui.DeleteObject(bmp2.GetHandle())

# ====== 截取客户区 (用 GetDC(hwnd)) ======
print()
print("⑤ 截取客户区 (GetDC HWND)")
hwnd_dc = win32gui.GetDC(hwnd)  # 获取客户区 DC
hwnd_mfc = win32ui.CreateDCFromHandle(hwnd_dc)
hwnd_mem = hwnd_mfc.CreateCompatibleDC()
bmp3 = win32ui.CreateBitmap()
bmp3.CreateCompatibleBitmap(hwnd_mfc, cr.right, cr.bottom)
hwnd_mem.SelectObject(bmp3)
gdi32.BitBlt(hwnd_mem.GetSafeHdc(), 0, 0, cr.right, cr.bottom,
             hwnd_mfc.GetSafeHdc(), 0, 0, SRCCOPY)
bits3 = bmp3.GetBitmapBits(True)
img3 = Image.frombuffer("RGB", (cr.right, cr.bottom), bits3, "raw", "BGRX", 0, 1)
img3.save(BASE_DIR / "data" / "diagnose_客户区.png")
print(f"  客户区截图: {cr.right} x {cr.bottom}  -> data/diagnose_客户区.png")

hwnd_mem.DeleteDC()
hwnd_mfc.DeleteDC()
win32gui.ReleaseDC(hwnd, hwnd_dc)
win32gui.DeleteObject(bmp3.GetHandle())

# ====== 截取全屏中 Edge 窗口覆盖的区域 ======
print()
print("⑥ 截取全屏中 Edge 所在区域（全屏裁剪）")
# 用全屏截图裁剪出 wr 区域
full_img2 = Image.open(BASE_DIR / "data" / "diagnose_全屏.png")
if wr.left >= 0 and wr.top >= 0 and wr.right <= screen_w and wr.bottom <= screen_h:
    crop = full_img2.crop((wr.left, wr.top, wr.right, wr.bottom))
    crop.save(BASE_DIR / "data" / "diagnose_全屏裁剪.png")
    print(f"  全屏裁剪成功: 从 ({wr.left},{wr.top}) 到 ({wr.right},{wr.bottom})")
else:
    print(f"  全屏裁剪失败: wr 超出了屏幕范围 ({wr.left},{wr.top})-({wr.right},{wr.bottom})")
    # 裁剪到屏幕内
    x1 = max(wr.left, 0)
    y1 = max(wr.top, 0)
    x2 = min(wr.right, screen_w)
    y2 = min(wr.bottom, screen_h)
    crop = full_img2.crop((x1, y1, x2, y2))
    crop.save(BASE_DIR / "data" / "diagnose_全屏裁剪.png")
    print(f"  调整为屏幕内裁剪: ({x1},{y1})-({x2},{y2})")

print()
print("=" * 55)
print("请在 VSCode 中打开 data/ 目录")
print("对比以下 4 张截图：")
print("  1. diagnose_全屏.png       ← 整个屏幕")
print("  2. diagnose_Dwm区域.png    ← Dwm 报告的窗口区域")
print("  3. diagnose_客户区.png     ← 客户区")
print("  4. diagnose_全屏裁剪.png   ← 全屏中裁剪出的窗口位置")
print()
print("告诉我哪张图的内容是完整的？")
print("=" * 55)
