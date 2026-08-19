from pathlib import Path
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILE_DIR = DATA_DIR / "edge_profile"

DATA_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)


with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        channel="msedge",
        headless=False,
        viewport={"width": 1440, "height": 900},
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        "https://www.zhipin.com/sem/10.html?_ts=1787103782801&sid=sem_bingpc&qudao=bing_pc_H120003UY5&plan=TCPA-%E5%BF%85%E5%BA%94-%E5%93%81%E7%89%8C&unit=%E4%BD%8E%E6%88%90%E6%9C%AC%E9%AB%98%E6%B6%88%E8%B4%B9%E8%AF%8D-1215&keyword=boss&msclkid=d8bf9faecc981d0d7ef7f52bc6bdfe6c",
        wait_until="domcontentloaded",
    )

    print("=" * 50)
    print("BOSS 自动化测试")
    print("=" * 50)
    print("当前网址：", page.url)
    print()
    print("请在浏览器中完成登录。")
    print("登录完成并进入 BOSS 沟通页面后，回到终端。")
    print()

    input("按 Enter 结束本次测试...")

    context.close()