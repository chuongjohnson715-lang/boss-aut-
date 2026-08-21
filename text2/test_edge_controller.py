from pathlib import Path

from core.edge_controller import EdgeController


BASE_DIR = Path(__file__).resolve().parent.parent

controller = EdgeController(
    BASE_DIR / "data"
)


print("=" * 50)
print("EdgeController 测试")
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

print("left:", rect[0])
print("top:", rect[1])
print("right:", rect[2])
print("bottom:", rect[3])


print()
print("④ 截图")

path = controller.capture(
    "edge_controller_test.png"
)

if path:
    print("截图成功")
    print("保存位置:", path)
else:
    print("截图失败")


print()
print("=" * 50)
print("测试结束")
print("=" * 50)