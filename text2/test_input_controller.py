import time
from pathlib import Path

from core.edge_controller import EdgeController
from core.input_controller import InputController


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


print("=" * 50)
print("BOSS 鼠标键盘控制测试")
print("=" * 50)

edge = EdgeController(DATA_DIR)
input_controller = InputController()

print()
print("① 查找 Edge")

if not edge.find_edge():
    print("Edge 查找失败")
    raise SystemExit

print("Edge 查找成功")
print("HWND:", edge.hwnd)

print()
print("② 激活 Edge")

if not edge.activate():
    print("Edge 激活失败")
    raise SystemExit

print("Edge 激活成功")

time.sleep(1)

print()
print("③ 当前鼠标位置")

print(input_controller.position())

print()
print("④ 移动鼠标")

input_controller.move(500, 500)

print("鼠标已经移动到：500, 500")

time.sleep(2)

print()
print("⑤ 键盘测试")

input_controller.press("esc")

print("ESC 已发送")

time.sleep(1)

print()
print("=" * 50)
print("测试结束")
print("=" * 50)