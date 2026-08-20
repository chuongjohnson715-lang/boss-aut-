from pathlib import Path
from playwright.sync_api import sync_playwright
import time


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = DATA_DIR / "edge_profile"

DATA_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

BOSS_URL = "https://www.zhipin.com/web/chat/index"


with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="msedge",
        headless=False,
        viewport={"width": 1440, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("=" * 60)
    print("BOSS 登录状态诊断")
    print("=" * 60)

    try:

        print("正在打开 BOSS...")

        page.goto(
            BOSS_URL,
            wait_until="domcontentloaded",
            timeout=30000
        )

        print("页面第一次加载完成")
        print("URL:", page.url)

        time.sleep(5)

        print()
        print("等待 5 秒后的状态：")
        print("URL:", page.url)
        print("Title:", page.title())

        print()
        print("页面文字前 1000 个字符：")

        try:
            text = page.locator("body").inner_text(timeout=10000)
            print(text[:1000])
        except Exception as e:
            print("读取页面文字失败：", repr(e))

        print()
        print("正在保存截图...")

        screenshot_path = DATA_DIR / "boss_login_debug.png"
        page.screenshot(
            path=str(screenshot_path),
            full_page=True
        )

        print("截图保存到：")
        print(screenshot_path)

        print()
        print("=" * 60)
        print("诊断结束")
        print("按 Enter 关闭浏览器")
        print("=" * 60)

        input()

    except Exception as e:

        print()
        print("=" * 60)
        print("发生异常")
        print("=" * 60)

        print(repr(e))

        input()

    finally:
        context.close()