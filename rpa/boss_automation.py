import json
import re
import threading
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.edge_controller import EdgeController
from data import db

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"
PROFILE_DIR = BASE_DIR / "data" / "edge_profile"


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


class BossAutomation:
    """BOSS 直聘候选人自动化流程。

    依赖 Playwright 控制 Edge 持久化配置，同时使用 EdgeController
    找到/激活当前 Edge 窗口，兼容本机已有窗口操作习惯。
    """

    def __init__(self, config=None, log_callback=None, stop_event=None):
        self.config = config or load_config()
        self.log_callback = log_callback or (lambda msg: print(msg))
        self.stop_event = stop_event or threading.Event()
        self.edge = EdgeController(BASE_DIR / "data")
        self.playwright = None
        self.context = None
        self.page = None
        self._candidate_index = 0

    # ------------------------------------------------------------------
    # 基础工具
    # ------------------------------------------------------------------
    def log(self, message, level="INFO"):
        self.log_callback(message)
        try:
            db.add_log(level, message)
        except Exception:
            pass

    def _should_stop(self):
        return self.stop_event.is_set()

    def _cfg(self, key, default=None):
        return self.config.get(key, default)

    def _selectors(self, key, default=""):
        return self._cfg("selectors", {}).get(key, default)

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def run(self):
        self.log("初始化数据库...")
        try:
            db.init_db()
            db.init_extensions()
        except Exception as e:
            self.log(f"数据库初始化失败: {e}", "ERROR")

        try:
            with sync_playwright() as p:
                self.playwright = p
                if not self._prepare_browser():
                    return False

                if not self._check_login():
                    self.log("BOSS 未登录，流程停止。请先登录 BOSS 直聘网页版。", "ERROR")
                    self._close_browser()
                    return False

                self._open_candidate_list()
                self._process_candidates()
                self._close_browser()
                return True
        except Exception as e:
            self.log(f"自动化运行异常: {e}", "ERROR")
            self._close_browser()
            return False

    def _prepare_browser(self):
        cdp_url = self._cfg("cdp_url", "").strip()
        if cdp_url:
            self.log(f"尝试连接已开启调试端口的 Edge: {cdp_url}")
            try:
                self.context = self.playwright.chromium.connect_over_cdp(cdp_url)
                self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
                self.log("CDP 连接成功")
            except Exception as e:
                self.log(f"CDP 连接失败: {e}", "ERROR")
                return False
        else:
            self.log("启动 Edge（使用 BOSS 专用配置）...")
            try:
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(PROFILE_DIR),
                    channel="msedge",
                    headless=False,
                    viewport={"width": 1440, "height": 900},
                    args=["--start-maximized"],
                )
                self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
                self.log("Edge 启动成功")
            except Exception as e:
                self.log(
                    "Edge 启动失败，常见原因是 data/edge_profile 已被正在运行的 Edge 占用。\n"
                    f"详细信息: {e}\n"
                    "请先关闭正在运行的 Edge，或在 config/config.json 中配置 CDP 连接已有 Edge。",
                    "ERROR"
                )
                return False

        # 启动后找到 Edge 窗口并激活（让用户看到操作过程）
        time.sleep(1.5)
        try:
            if self.edge.find_edge():
                self.edge.activate()
                self.log("已激活 Edge 窗口")
            else:
                self.log("未找到 Edge 窗口，继续后台流程", "WARN")
        except Exception as e:
            self.log(f"激活 Edge 窗口失败（不影响流程）: {e}", "WARN")

        return True

    def _close_browser(self):
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        self.context = None
        self.page = None

    # ------------------------------------------------------------------
    # 登录与候选列表
    # ------------------------------------------------------------------
    def _check_login(self):
        boss_url = self._cfg("boss_url", "https://www.zhipin.com/web/chat/index")
        self.log(f"打开 BOSS 页面: {boss_url}")
        try:
            self.page.goto(boss_url, wait_until="domcontentloaded", timeout=60000)
            self.page.wait_for_timeout(2500)
        except Exception as e:
            self.log(f"打开 BOSS 页面失败: {e}", "ERROR")
            return False

        url = (self.page.url or "").lower()
        if "login" in url or "passport" in url:
            self.log("检测到登录跳转（URL 含 login/passport）")
            return False

        try:
            body_text = self.page.locator("body").inner_text(timeout=5000)
        except Exception:
            body_text = ""

        login_markers = ["扫码登录", "请登录", "账号密码登录", "登录后查看"]
        for marker in login_markers:
            if marker in body_text:
                self.log(f"检测到未登录特征: {marker}")
                return False

        self.log("BOSS 已登录")
        return True

    def _open_candidate_list(self):
        url = self._cfg("candidate_list_url") or self._cfg("boss_url")
        self.log(f"进入候选人列表: {url}")
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            self.page.wait_for_timeout(2000)
        except Exception as e:
            self.log(f"打开候选人列表失败: {e}", "ERROR")

    # ------------------------------------------------------------------
    # 候选人遍历
    # ------------------------------------------------------------------
    def _process_candidates(self):
        max_candidates = int(self._cfg("max_candidates", 50) or 50)
        processed = 0
        self._candidate_index = 0

        while processed < max_candidates and not self._should_stop():
            self.log(f"--- 开始处理第 {self._candidate_index + 1} 位候选人 ---")

            if not self._select_candidate(self._candidate_index):
                self.log("没有更多候选人，结束遍历", "WARN")
                break

            info = self._extract_candidate_info()
            if not info.get("name"):
                self.log("未能读取到候选人姓名，可能页面结构变化，跳过该候选人", "WARN")
                self._candidate_index += 1
                processed += 1
                continue

            self.log(
                f"候选人: {info.get('name')} | {info.get('school') or '未知学校'} "
                f"| {info.get('education') or '未知学历'} | {info.get('major') or '未知专业'}"
            )

            # 筛选未回复的候选人：已联系过（数据库已有常用语1 记录）则跳过
            if self._cfg("skip_contacted", True):
                try:
                    if db.is_contacted(info.get("name"), info.get("position")):
                        self.log(
                            f"候选人 {info.get('name')} 已联系过（数据库有记录），"
                            "跳过，继续下一个候选人"
                        )
                        self._candidate_index += 1
                        processed += 1
                        continue
                except Exception as e:
                    self.log(f"查询候选人联系记录失败（本次不跳过）: {e}", "WARN")

            # 发送常用语1
            self._send_common_message(1)
            db.upsert_candidate(
                name=info.get("name"),
                position=info.get("position"),
                education=info.get("education"),
                school=info.get("school"),
                major=info.get("major"),
                gender=info.get("gender"),
                status="message1_sent",
                message1_sent=1,
                source="boss",
                remark="已发送常用语1"
            )

            # 等待对方回复/简历
            has_resume = self._wait_for_reply_or_resume()
            if not has_resume:
                self.log("未检测到简历/有效回复，等待或跳过该候选人", "WARN")
                db.upsert_candidate(
                    name=info.get("name"),
                    position=info.get("position"),
                    education=info.get("education"),
                    school=info.get("school"),
                    major=info.get("major"),
                    gender=info.get("gender"),
                    status="waiting",
                    message1_sent=1,
                    resume_received=0,
                    source="boss",
                    remark="未收到简历，等待/跳过"
                )
                self._candidate_index += 1
                processed += 1
                continue

            # 已收到简历 -> 发送常用语2
            self.log("检测到简历，发送常用语2")
            self._send_common_message(2)
            db.upsert_candidate(
                name=info.get("name"),
                position=info.get("position"),
                education=info.get("education"),
                school=info.get("school"),
                major=info.get("major"),
                gender=info.get("gender"),
                status="resume_received",
                message1_sent=1,
                resume_received=1,
                message2_sent=1,
                source="boss",
                remark="已收到简历并发送常用语2"
            )

            # 再次获取候选人信息（可能简历后有更多字段）
            info = self._extract_candidate_info()

            # 学历判断
            school_type, edu_ok = self._judge_education(info)
            if not edu_ok:
                self.log(f"学历/学校不符合 985/强211 白名单: {info.get('school')}", "WARN")
                db.upsert_candidate(
                    name=info.get("name"),
                    position=info.get("position"),
                    education=info.get("education"),
                    school=info.get("school"),
                    major=info.get("major"),
                    gender=info.get("gender"),
                    status="skipped_education",
                    message1_sent=1,
                    resume_received=1,
                    message2_sent=1,
                    qualified=0,
                    school_type=school_type,
                    source="boss",
                    remark="学历不符合，跳过"
                )
                self._candidate_index += 1
                processed += 1
                continue

            self.log(f"学校/学历符合: {info.get('school')} ({school_type})，进入候选池")

            # 其他岗位条件
            condition_ok, reason = self._check_other_conditions(info)
            if not condition_ok:
                self.log(f"其他岗位条件不符合: {reason}", "WARN")
                db.upsert_candidate(
                    name=info.get("name"),
                    position=info.get("position"),
                    education=info.get("education"),
                    school=info.get("school"),
                    major=info.get("major"),
                    gender=info.get("gender"),
                    status="skipped_conditions",
                    message1_sent=1,
                    resume_received=1,
                    message2_sent=1,
                    qualified=0,
                    school_type=school_type,
                    source="boss",
                    remark=reason or "其他岗位条件不符合"
                )
                self._candidate_index += 1
                processed += 1
                continue

            # 符合 -> 置顶
            pinned = self._pin_candidate()
            db.upsert_candidate(
                name=info.get("name"),
                position=info.get("position"),
                education=info.get("education"),
                school=info.get("school"),
                major=info.get("major"),
                gender=info.get("gender"),
                status="pinned" if pinned else "qualified_not_pinned",
                message1_sent=1,
                resume_received=1,
                message2_sent=1,
                qualified=1,
                pinned=1 if pinned else 0,
                school_type=school_type,
                source="boss",
                remark="符合条件，已置顶" if pinned else "符合条件，但未找到置顶按钮"
            )

            self._candidate_index += 1
            processed += 1
            self.log(f"已完成 {processed}/{max_candidates} 位候选人")

        self.log("候选人遍历结束")

    def _select_candidate(self, index):
        selector = self._selectors("candidate_item")
        if not selector:
            self.log("未配置候选人列表选择器", "ERROR")
            return False

        try:
            locator = self.page.locator(selector)
            count = locator.count()
            if count == 0:
                return False
            if index >= count:
                return False
            locator.nth(index).click(timeout=8000)
            self.page.wait_for_timeout(1200)
            return True
        except Exception as e:
            self.log(f"选择候选人失败: {e}", "WARN")
            return False

    # ------------------------------------------------------------------
    # 信息提取
    # ------------------------------------------------------------------
    def _extract_candidate_info(self):
        info = {
            "name": "",
            "position": "",
            "education": "",
            "school": "",
            "major": "",
            "gender": "",
        }

        try:
            body_text = self.page.locator("body").inner_text(timeout=5000)
        except Exception:
            body_text = ""

        # 姓名：优先结构化选择器
        name_selector = self._selectors("candidate_name")
        if name_selector:
            try:
                first = self.page.locator(name_selector).first
                if first.count() > 0:
                    name = first.inner_text(timeout=3000).strip().splitlines()[0].strip()
                    if name and len(name) <= 20:
                        info["name"] = name
            except Exception:
                pass

        if not info["name"]:
            info["name"] = self._regex_extract(body_text, r"([\u4e00-\u9fa5]{2,4}(?:先生|女士)?)")

        # 性别
        gender = self._regex_extract(body_text, r"(男|女)")
        if gender in ("男", "女"):
            info["gender"] = gender

        # 学历
        edu_match = re.search(r"(博士|硕士|本科|大专|高中|中技|中专)", body_text)
        if edu_match:
            info["education"] = edu_match.group(1)

        # 学校：在白名单中查找
        whitelist = self._cfg("education_check", {}).get("whitelist", [])
        for school in whitelist:
            if school and school in body_text:
                info["school"] = school
                break

        if not info["school"]:
            school_match = re.search(r"(?:毕业于|来自|学校[:：]?)\s*([\u4e00-\u9fa5A-Za-z0-9（）()·]{2,30})", body_text)
            if school_match:
                info["school"] = school_match.group(1).strip()

        # 专业
        major_match = re.search(r"(?:专业[:：]?|主修[:：]?)\s*([\u4e00-\u9fa5A-Za-z0-9（）()·]{2,30})", body_text)
        if major_match:
            info["major"] = major_match.group(1).strip()
        else:
            major_match = re.search(r"([\u4e00-\u9fa5]{2,20}(?:工程|科学|技术|管理|经济|金融|设计|文学|法学|医学|教育|数学|物理|化学|生物|计算机|软件|自动化|机械|材料|电子|通信|会计|市场营销|人力资源))", body_text)
            if major_match:
                info["major"] = major_match.group(1)

        # 职位/求职意向
        pos_match = re.search(r"(?:求职意向|应聘岗位|意向岗位|职位)[:：]?\s*([^\n，,。]{2,30})", body_text)
        if pos_match:
            info["position"] = pos_match.group(1).strip()

        if not info["position"]:
            try:
                title = self.page.title() or ""
                if title:
                    info["position"] = title.split("_")[0].strip()
            except Exception:
                pass

        return info

    @staticmethod
    def _regex_extract(text, pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""

    # ------------------------------------------------------------------
    # 消息发送
    # ------------------------------------------------------------------
    def _send_common_message(self, message_no):
        key = "common_message_1" if message_no == 1 else "common_message_2"
        text = self._cfg(key, "")
        if not text:
            self.log(f"未配置常用语{message_no}", "WARN")
            return False

        self.log(f"发送常用语{message_no}: {text}")
        try:
            input_selector = self._selectors("message_input")
            if input_selector:
                locator = self.page.locator(input_selector).first
                if locator.count() > 0:
                    tag = (locator.evaluate("el => el.tagName") or "").lower()
                    if tag in ("input", "textarea"):
                        locator.fill(text, timeout=5000)
                    else:
                        locator.click(timeout=5000)
                        self.page.keyboard.type(text, delay=20)
                else:
                    self._type_via_keyboard(text)
            else:
                self._type_via_keyboard(text)

            self._press_send()
            self.page.wait_for_timeout(800)
            return True
        except Exception as e:
            self.log(f"发送常用语{message_no}失败: {e}", "ERROR")
            return False

    def _type_via_keyboard(self, text):
        self.page.keyboard.type(text, delay=20)

    def _press_send(self):
        send_selector = self._selectors("send_button")
        if send_selector:
            try:
                btn = self.page.locator(send_selector).first
                if btn.count() > 0:
                    btn.click(timeout=3000)
                    return
            except Exception:
                pass
        # 常见聊天输入框按 Enter 发送
        try:
            self.page.keyboard.press("Enter")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 等待回复/简历
    # ------------------------------------------------------------------
    def _wait_for_reply_or_resume(self):
        wait_seconds = int(self._cfg("wait_reply_seconds", 45) or 45)
        resume_keywords = [
            "发来一份简历", "发来了简历", "收到简历", "简历已发送",
            "已发送简历", "我的简历", "附件", "PDF", "DOC", "DOCX",
            "下载简历", "查看简历附件"
        ]
        self.log(f"等待对方回复/简历（最长 {wait_seconds} 秒）...")

        start = time.time()
        while time.time() - start < wait_seconds and not self._should_stop():
            try:
                body_text = self.page.locator("body").inner_text(timeout=3000)
                for kw in resume_keywords:
                    if kw.lower() in body_text.lower():
                        self.log(f"检测到简历特征: {kw}")
                        return True
            except Exception:
                pass
            self.page.wait_for_timeout(3000)
        return False

    # ------------------------------------------------------------------
    # 学历与条件判断
    # ------------------------------------------------------------------
    def _judge_education(self, info):
        edu_cfg = self._cfg("education_check", {})
        if not edu_cfg.get("enable", True):
            return "disabled", True

        school = (info.get("school") or "").strip()
        whitelist = edu_cfg.get("whitelist", [])
        if school in whitelist:
            return "985/强211", True

        # 如果页面明确带“985/211”等标识也可视为符合
        try:
            body_text = self.page.locator("body").inner_text(timeout=3000)
        except Exception:
            body_text = ""
        if "985" in body_text or ("211" in body_text and "双一流" in body_text):
            return "985/211标识", True

        return "普通", False

    def _check_other_conditions(self, info):
        cond_cfg = self._cfg("other_conditions", {})
        if not cond_cfg.get("enable", True):
            return True, "未启用其他条件"

        try:
            body_text = self.page.locator("body").inner_text(timeout=3000)
        except Exception:
            body_text = ""

        require = cond_cfg.get("require_keywords", [])
        exclude = cond_cfg.get("exclude_keywords", [])

        for kw in require:
            if kw and kw not in body_text and kw not in str(info):
                return False, f"缺少必要条件: {kw}"

        for kw in exclude:
            if kw and kw in body_text:
                return False, f"命中排除条件: {kw}"

        return True, "符合其他条件"

    # ------------------------------------------------------------------
    # 置顶
    # ------------------------------------------------------------------
    def _pin_candidate(self):
        pin_selector = self._selectors("pin_button")
        if not pin_selector:
            self.log("未配置置顶按钮选择器", "WARN")
            return False
        try:
            btn = self.page.locator(pin_selector).first
            if btn.count() == 0:
                self.log("未找到置顶按钮", "WARN")
                return False
            btn.click(timeout=5000)
            self.page.wait_for_timeout(800)
            self.log("已点击置顶")
            return True
        except Exception as e:
            self.log(f"置顶失败: {e}", "WARN")
            return False
