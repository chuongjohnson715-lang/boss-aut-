import win32gui
from PIL import ImageGrab
from pathlib import Path
import unicodedata

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

print("=" * 50)
print("Edge 窗口截图测试")
print("=" * 50)

edge_windows = []


def normalize_text(text):
    text = unicodedata.normalize("NFKC", text)

    invisible_chars = [
        "\u200b",
        "\u200c",
        "\u200d",
        "\u2060",
        "\ufeff",
    ]

    for char in invisible_chars:
        text = text.replace(char, "")

    return text


def enum_windows(hwnd, _):
    if not win32gui.IsWindowVisible(hwnd):
        return

    title = win32gui.GetWindowText(hwnd)

    if not title.strip():
        return

    normalized_title = normalize_text(title)

    if "Microsoft Edge" in normalized_title:
        edge_windows.append((hwnd, title))


win32gui.EnumWindows(enum_windows, None)


print()
print(f"检测到 Edge 窗口数量：{len(edge_windows)}")

for hwnd, title in edge_windows:
    print()
    print("HWND:", hwnd)
    print("标题:", title)


if edge_windows:
    hwnd, title = edge_windows[0]

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)

    print()
    print("当前使用的 Edge：")
    print("HWND:", hwnd)
    print("窗口坐标:")
    print("左:", left)
    print("上:", top)
    print("右:", right)
    print("下:", bottom)

    width = right - left
    height = bottom - top

    print()
    print("窗口大小:")
    print("宽:", width)
    print("高:", height)

    screenshot_path = DATA_DIR / "edge_test.png"

    image = ImageGrab.grab(
        bbox=(left, top, right, bottom)
    )

    image.save(screenshot_path)

    print()
    print("截图成功")
    print("保存位置:")
    print(screenshot_path)

else:
    print()
    print("没有找到 Edge 窗口")


print()
print("=" * 50)
print("检测结束")
print("=" * 50)