from pathlib import Path
from core.edge_controller import EdgeController

BASE_DIR = Path(__file__).resolve().parent.parent
controller = EdgeController(BASE_DIR / "data")

print("=" * 50)
print("capture_dwm() 测试")
print("=" * 50)

if not controller.find_edge():
    print("Edge 查找失败")
    raise SystemExit
print("HWND:", controller.hwnd)

controller.activate()

print()
print("① 原 capture() 对照")
path1 = controller.capture("capture_对照.png")
if path1:
    print(f"  保存: {path1}")
else:
    print("  失败")

print()
print("② 新 capture_dwm()")
path2 = controller.capture_dwm("capture_dwm_结果.png")
if path2:
    img = Path(BASE_DIR / "data" / "capture_dwm_结果.png")
    if img.exists():
        from PIL import Image
        im = Image.open(str(img))
        print(f"  保存: {path2}")
        print(f"  尺寸: {im.width} x {im.height}")
else:
    print("  失败")

print()
print("=" * 50)
print("请在 data/ 目录下对比两张截图")
print("  capture_对照.png     ← 原方法 (GetWindowRect)")
print("  capture_dwm_结果.png ← 新方法 (DWM) ← 应该完整")
print("=" * 50)
