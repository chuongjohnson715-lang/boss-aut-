
import json
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from pathlib import Path

from rpa.boss_automation import BossAutomation, load_config


class BossApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BOSS 直聘自动化")
        self.root.geometry("760x520")

        self.config = load_config()
        self.worker = None
        self.stop_event = threading.Event()

        self._build_ui()
        self._log("程序已启动，点击「启动自动化」开始。")

    def _build_ui(self):
        top = tk.Frame(self.root, padx=10, pady=8)
        top.pack(fill="x")

        tk.Button(top, text="启动自动化", command=self.start, width=14).pack(side="left", padx=4)
        tk.Button(top, text="停止", command=self.stop, width=10).pack(side="left", padx=4)
        tk.Button(top, text="重新加载配置", command=self.reload_config, width=14).pack(side="left", padx=4)

        info = tk.Frame(self.root, padx=10, pady=4)
        info.pack(fill="x")
        tk.Label(info, text="常用语1:").grid(row=0, column=0, sticky="e")
        self.msg1_var = tk.StringVar(value=self.config.get("common_message_1", ""))
        tk.Entry(info, textvariable=self.msg1_var, width=70).grid(row=0, column=1, sticky="we", padx=4)

        tk.Label(info, text="常用语2:").grid(row=1, column=0, sticky="e")
        self.msg2_var = tk.StringVar(value=self.config.get("common_message_2", ""))
        tk.Entry(info, textvariable=self.msg2_var, width=70).grid(row=1, column=1, sticky="we", padx=4)

        tk.Label(info, text="最多处理:").grid(row=2, column=0, sticky="e")
        self.max_var = tk.StringVar(value=str(self.config.get("max_candidates", 50)))
        tk.Entry(info, textvariable=self.max_var, width=10).grid(row=2, column=1, sticky="w", padx=4)

        self.log_text = scrolledtext.ScrolledText(self.root, height=20, state="disabled", font=("Microsoft YaHei", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=8)

    def _log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def reload_config(self):
        self.config = load_config()
        self.msg1_var.set(self.config.get("common_message_1", ""))
        self.msg2_var.set(self.config.get("common_message_2", ""))
        self.max_var.set(str(self.config.get("max_candidates", 50)))
        self._log("配置已重新加载")

    def start(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("提示", "自动化已经在运行中")
            return

        self.config["common_message_1"] = self.msg1_var.get().strip()
        self.config["common_message_2"] = self.msg2_var.get().strip()
        try:
            self.config["max_candidates"] = int(self.max_var.get().strip() or 50)
        except ValueError:
            self.config["max_candidates"] = 50

        self.stop_event.clear()
        self.worker = threading.Thread(target=self._run_worker, daemon=True)
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        self._log("正在请求停止...")

    def _run_worker(self):
        automation = BossAutomation(
            config=self.config,
            log_callback=self._log,
            stop_event=self.stop_event,
        )
        try:
            automation.run()
        except Exception as e:
            self._log(f"发生未处理异常: {e}")


def main():
    root = tk.Tk()
    app = BossApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
