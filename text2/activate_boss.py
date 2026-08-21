import time
import win32gui
import win32con


def find_edge_windows():
    edge_windows = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)

        if "Microsoft" in title and "Edge" in title:
            edge_windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)

    return edge_windows


def activate_window(hwnd):
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    win32gui.SetForegroundWindow(hwnd)


print("=" * 50)
print("BOSS Edge 窗口激活测试")
print("=" * 50)

windows = find_edge_windows()

print()
print("检测到 Edge 窗口数量：", len(windows))

if len(windows) == 0:
    print("没有找到 Edge")
    print("程序停止，不执行任何操作")

elif len(windows) > 1:
    print("检测到多个 Edge 窗口")
    print()
    
    for i, (hwnd, title) in enumerate(windows, 1):
        print(f"[{i}] HWND: {hwnd}")
        print(f"    标题: {title}")

    print()
    print("为了安全，本次不自动选择")
    print("程序停止")

else:
    hwnd, title = windows[0]

    print()
    print("找到唯一 Edge：")
    print("HWND:", hwnd)
    print("标题:", title)

    print()
    print("正在激活 Edge...")

    activate_window(hwnd)

    time.sleep(1)

    current_hwnd = win32gui.GetForegroundWindow()

    print()
    print("当前前台窗口 HWND:", current_hwnd)

    if current_hwnd == hwnd:
        print("Edge 激活成功")
    else:
        print("Edge 激活失败")
        print("程序停止")

print()
print("=" * 50)
print("测试结束")
print("=" * 50)