import tkinter as tk
from tkinter import filedialog, messagebox

from core.engine import MangoEngine
from core.loop_manager import LoopManager


class MangoUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MANGO v26")
        self.root.geometry("800x500")

        # 엔진 / 루프
        self.engine = MangoEngine()
        self.loop = LoopManager(self.update_status)

        self.attachments = []

        # ===== 상단 상태 =====
        self.status_var = tk.StringVar(value="idle")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var, font=("Arial", 14)
        )
        self.status_label.pack(pady=10)

        # ===== 입력창 =====
        self.entry = tk.Entry(self.root, width=80)
        self.entry.pack(pady=10)

        # ===== 버튼 영역 =====
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.attach_btn = tk.Button(
            btn_frame, text="첨부", width=10, command=self.add_file
        )
        self.attach_btn.grid(row=0, column=0, padx=5)

        self.run_btn = tk.Button(
            btn_frame, text="실행", width=10, command=self.run_task
        )
        self.run_btn.grid(row=0, column=1, padx=5)

        self.stop_btn = tk.Button(
            btn_frame, text="중지", width=10, command=self.stop_task
        )
        self.stop_btn.grid(row=0, column=2, padx=5)

        # ===== 첨부 리스트 =====
        self.file_list = tk.Listbox(self.root, height=10)
        self.file_list.pack(fill="both", expand=True, padx=20, pady=10)

    # ===== 기능 =====

    def add_file(self):
        file = filedialog.askopenfilename()
        if file:
            self.attachments.append(file)
            self.file_list.insert(tk.END, file)

    def run_task(self):
        command = self.entry.get().strip()

        if not command:
            messagebox.showwarning("경고", "명령을 입력하세요.")
            return

        if not self.attachments:
            messagebox.showwarning("경고", "첨부 파일이 필요합니다.")
            return

        self.loop.start(self.execute, command)

    def stop_task(self):
        self.loop.stop()
        self.update_status("idle", "중지됨")

    def execute(self, command):
        result = self.engine.execute_once(command, self.attachments)

        if result["status"] == "NEEDS_SPEC":
            messagebox.showinfo(
                "시방서 생성",
                f"시방서 파일 생성됨:\n{result['spec_path']}",
            )
            return "DONE"

        return "DONE"

    def update_status(self, state, msg):
        self.status_var.set(f"{state} | {msg}")

    def run(self):
        self.root.mainloop()
