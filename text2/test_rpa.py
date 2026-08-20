import win32gui

print("=" * 50)
print("Windows 窗口检测")
print("=" * 50)

def enum_windows(hwnd, _):
    if not win32gui.IsWindowVisible(hwnd):
        return

    title = win32gui.GetWindowText(hwnd)

    if title.strip():
        print(f"HWND: {hwnd} | 标题: {title}")

win32gui.EnumWindows(enum_windows, None)

print()
print("=" * 50)
print("检测结束")
print("=" * 50)
saf