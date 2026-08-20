from pathlib import Path
from playwright.sync_api import sync_playwright
import time


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = DATA_DIR / "edge_profile"

DATA_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

BOSS_URL = "https://www.zhipin.com/"


with sync_playwright() as p:

    print("=" * 60)
    print("BOSS 浏览器稳定性诊断")
    print("=" * 60)

    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="msedge",
        headless=False,
        viewport={"width": 1440, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()

    # 监听页面导航
    page.on(
        "framenavigated",
        lambda frame: print(
            "[NAVIGATED]",
            frame.url
        )
    )

    # 监听页面关闭
    page.on(
        "close",
        lambda: print("[PAGE CLOSED]")
    )

    # 监听新页面
    context.on(
        "page",
        lambda new_page: print(
            "[NEW PAGE]",
            new_page.url
        )
    )

    print()
    print("正在打开 BOSS...")

    page.goto(
        BOSS_URL,
        wait_until="domcontentloaded",
        timeout=30000
    )

    print()
    print("第一次加载完成")
    print("URL:", page.url)
    print("Title:", page.title())

    print()
    print("=" * 60)
    print("现在什么都不要操作")
    print("不要登录")
    print("不要点击")
    print("不要按 Enter")
    print("=" * 60)

    # 持续观察 30 秒
    for i in range(30):

        time.sleep(1)

        try:
            print(
                f"[{i + 1:02d}s]",
                "URL =", page.url,
                "| TITLE =", page.title()
            )

        except Exception as e:
            print(
                f"[{i + 1:02d}s]",
                "页面读取失败:",
                repr(e)
            )
            break

    print()
    print("=" * 60)
    print("诊断结束")
    print("=" * 60)

    input("按 Enter 关闭浏览器...")

    context.close()