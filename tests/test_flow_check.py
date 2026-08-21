"""v2.08 回归测试：验证「筛选未回复候选人」与「Edge 窗口优先 BOSS 页面」。

运行方式：
    "aut3.11（64）.venv\\Scripts\\python.exe" tests\\test_flow_check.py
"""
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

passed = 0
failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")


# ------------------------------------------------------------------
# 1. db.is_contacted（使用临时数据库，不污染 data/boss.db）
# ------------------------------------------------------------------
print("== db.is_contacted ==")
import data.db as db

tmp = Path(tempfile.mkdtemp()) / "test_boss.db"
db.DB_PATH = tmp
db.init_db()
db.init_extensions()

db.upsert_candidate(name="张三", position="后端工程师", status="message1_sent", message1_sent=1, source="boss")
check("已发常用语1 的候选人 → is_contacted=True", db.is_contacted("张三", "后端工程师") is True)

db.upsert_candidate(name="王五", position="产品经理", status="waiting", message1_sent=0, resume_received=0)
check("有记录但未发常用语1 → is_contacted=False", db.is_contacted("王五", "产品经理") is False)

check("从未见过的候选人 → is_contacted=False", db.is_contacted("李四", "前端工程师") is False)

# ------------------------------------------------------------------
# 2. EdgeController._is_boss_window（纯字符串逻辑，无需真实窗口）
# ------------------------------------------------------------------
print("== EdgeController._is_boss_window ==")
try:
    from core.edge_controller import EdgeController
except Exception as e:  # 依赖缺失时跳过，不影响其它检查
    print(f"  [SKIP] 无法导入 edge_controller: {e}")
else:
    check("标题「BOSS直聘-职位详情-XXX」→ True",
          EdgeController._is_boss_window("BOSS直聘-职位详情-XXX") is True)
    check("标题含 zhipin → True",
          EdgeController._is_boss_window("Boss直聘 · zhipin.com 聊天") is True)
    check("普通网页标题 → False",
          EdgeController._is_boss_window("百度一下，你就知道") is False)
    check("空标题 → False", EdgeController._is_boss_window("") is False)
    check("None 标题 → False", EdgeController._is_boss_window(None) is False)

# ------------------------------------------------------------------
# 3. config 新字段存在性
# ------------------------------------------------------------------
print("== config.json ==")
import json

cfg = json.loads((BASE_DIR / "config" / "config.json").read_text(encoding="utf-8"))
check("存在 skip_contacted 且默认 true", cfg.get("skip_contacted") is True)

print(f"\n结果: {passed} 通过, {failed} 失败")
sys.exit(1 if failed else 0)
