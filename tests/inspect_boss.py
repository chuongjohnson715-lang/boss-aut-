from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = BASE_DIR / "data" / "edge_profile"


with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="msedge",
        headless=False,
        viewport={"width": 1440, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        "https://www.zhipin.com/web/chat/index",
        wait_until="domcontentloaded",
    )

    print("=" * 60)
    print("BOSS 页面 DOM 侦察")
    print("=" * 60)

    input("请登录 BOSS，并点击一个候选人，然后按 Enter...")

    print("\n当前网址：")
    print(page.url)

    print("\n当前页面标题：")
    print(page.title())

    print("\n当前页面文本：")
    print("-" * 60)

    text = page.locator("body").inner_text()

    print(text[:8000])

    print("-" * 60)

    input("\n侦察完成，按 Enter 关闭浏览器...")

    context.close()