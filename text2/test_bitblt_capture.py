from pathlib import Path

import ctypes
from ctypes import wintypes
import win32gui
import win32ui
from PIL import Image

from core.edge_controller import EdgeController


BASE_DIR = Path(__file__).resolve().parent.parent
controller = EdgeController(BASE_DIR / "data")


print("=" * 50)
print("BitBlt 截图测试")
print("=" * 50)


print()
print("① 查找 Edge")

if not controller.find_edge():
    print("Edge 查找失败")
    raise SystemExit

print("Edge 查找成功")
print("HWND:", controller.hwnd)
print("标题:", controller.title)


print()
print("② 激活 Edge")

if controller.activate():
    print("Edge 激活成功")
else:
    print("Edge 激活失败")
    raise SystemExit


print()
print("③ 获取窗口坐标")

rect = controller.get_rect()
left, top, right, bottom = rect
width = right - left
height = bottom - top

print(f"GetWindowRect: left={left} top={top} right={right} bottom={bottom}")
print(f"窗口矩形尺寸: {width} x {height}")


hwnd = controller.hwnd
user32 = ctypes.windll.user32

# 获取客户区坐标
cr = wintypes.RECT()
user32.GetClientRect(hwnd, ctypes.byref(cr))
client_w = cr.right - cr.left
client_h = cr.bottom - cr.top

# 客户区左上角屏幕坐标
pt = wintypes.POINT(0, 0)
user32.ClientToScreen(hwnd, ctypes.byref(pt))
client_x = pt.x
client_y = pt.y

print(f"GetClientRect: left={cr.left} top={cr.top} right={cr.right} bottom={cr.bottom}")
print(f"客户区尺寸: {client_w} x {client_h}")
print(f"客户区屏幕坐标: ({client_x}, {client_y})")


print()
print("④ PrintWindow 对照（从窗口矩形）")

pw_path = controller.capture("edge_printwindow_对照.png")
if pw_path:
    print(f"PrintWindow 截图已保存: {pw_path}")
else:
    print("PrintWindow 截图失败")


print()
print("⑤ BitBlt 截图（从客户区）")

screen_dc = win32gui.GetDC(0)
screen_mfc = win32ui.CreateDCFromHandle(screen_dc)
mem_dc = screen_mfc.CreateCompatibleDC()

bitmap = win32ui.CreateBitmap()
bitmap.CreateCompatibleBitmap(screen_mfc, client_w, client_h)
mem_dc.SelectObject(bitmap)

gdi32 = ctypes.windll.gdi32
SRCCOPY = 0x00CC0020

blit_ok = gdi32.BitBlt(
    mem_dc.GetSafeHdc(),
    0, 0, client_w, client_h,
    screen_mfc.GetSafeHdc(),
    client_x, client_y,
    SRCCOPY
)

if not blit_ok:
    print("BitBlt 失败")
    win32gui.DeleteObject(bitmap.GetHandle())
    mem_dc.DeleteDC()
    screen_mfc.DeleteDC()
    win32gui.ReleaseDC(0, screen_dc)
    raise SystemExit

print("BitBlt 成功")

bmp_bits = bitmap.GetBitmapBits(True)
img = Image.frombuffer(
    "RGB",
    (client_w, client_h),
    bmp_bits, "raw", "BGRX", 0, 1
)

save_path = BASE_DIR / "data" / "edge_bitblt_test.png"
img.save(save_path)
print(f"截图尺寸: {client_w} x {client_h}")
print(f"BitBlt 截图已保存: {save_path}")

# 清理
win32gui.DeleteObject(bitmap.GetHandle())
mem_dc.DeleteDC()
screen_mfc.DeleteDC()
win32gui.ReleaseDC(0, screen_dc)


print()
print("=" * 50)
print("测试结束")
print("=" * 50)


print()
print("=== 根因分析 ===")
print()
print(f"屏幕: 2048 x 1280")
print(f"窗口矩形 (GetWindowRect): 2062 x 1246  ← 包含不可见的边框阴影")
print(f"客户区 (GetClientRect):    {client_w} x {client_h}  ← 实际可见内容")
print()
print("Edge 窗口处于最大化状态。Windows 最大化窗口的边框阴影")
print("延伸到了屏幕可见区域之外（左边和上边各 -7px），")
print("导致 GetWindowRect 返回的尺寸偏大。")
print()
print("原有的 capture() 使用 GetWindowRect 的尺寸来截图，")
print("截取的是 2062 x 1246 的完整窗口矩形，")
print("但实际上屏幕只显示了 2048 x 1232（客户区），")
print("所以右下角约 1/5 的内容其实是窗口边框阴影在屏幕外的部分。")
print()
print("两种截图方法对比")
print()
print("【PrintWindow（现有 capture）】")
print("  原理: 向窗口发送 WM_PRINT 消息，让窗口自己绘制到目标 DC。")
print("  适合: 窗口被遮挡、最小化、甚至不可见时仍可截图。")
print("  限制: 部分窗口（尤其是硬件加速的 Edge/Chrome）")
print("       不响应 WM_PRINT，导致内容缺失或黑屏。")
print("  典型场景: 后台自动化截图、窗口不可见时抓取。")
print()
print("【BitBlt（本测试）】")
print("  原理: 直接从显存/屏幕 DC 复制像素数据，")
print("       截取的是实际显示在屏幕上的画面。")
print("  适合: 窗口可见时截取完整视觉效果，")
print("       包括硬件加速渲染的内容。")
print("  限制: 窗口必须可见且未被完全遮挡；")
print("       窗口移出屏幕区域（负坐标）时可能截不到。")
print("  典型场景: 前端测试、所见即所得的截图。")
