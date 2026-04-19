import os
import threading
import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox


class MangoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MANGO_v26")
        self.root.geometry("1220x760")

        self.attached_files = []
        self.running = False

        # 상태
        self.current_task_var = tk.StringVar(value="idle")

        # 상단
        top_frame = tk.Frame(root)
        top_frame.pack(fill="x", padx=10, pady=10)

        self.status_label = tk.Label(top_frame, textvariable=self.current_task_var, font=("Arial", 14))
        self.status_label.pack(anchor="w")

        self.progress = tk.Label(top_frame, bg="green", height=1)
        self.progress.pack(fill="x", pady=5)

        # 본문
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 좌측
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        tk.Label(left_frame, text="대화 / 보고").pack(anchor="w")

        self.log = tk.Text(left_frame, height=20)
        self.log.pack(fill="both", expand=True)

        input_frame = tk.Frame(left_frame)
        input_frame.pack(fill="x")

        self.entry = tk.Entry(input_frame)
        self.entry.pack(side="left", fill="x", expand=True)

        send_btn = tk.Button(input_frame, text="보내기", command=self.handle_input)
        send_btn.pack(side="right")

        attach_frame = tk.Frame(left_frame)
        attach_frame.pack(fill="x", pady=5)

        self.attach_label = tk.Label(attach_frame, text="첨부 없음")
        self.attach_label.pack(side="left")

        tk.Button(attach_frame, text="파일 첨부", command=self.attach_files).pack(side="right")
        tk.Button(attach_frame, text="첨부 비움", command=self.clear_files).pack(side="right")

        # 우측
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="y")

        tk.Label(right_frame, text="상태 / 제어").pack()

        tk.Button(right_frame, text="루프 ON", command=self.loop_on).pack(fill="x")
        tk.Button(right_frame, text="루프 OFF", command=self.loop_off).pack(fill="x")
        tk.Button(right_frame, text="자동 루프 실행", command=self.run_loop).pack(fill="x")

        tk.Button(right_frame, text="workspace 열기", command=lambda: os.startfile("workspace")).pack(fill="x")
        tk.Button(right_frame, text="logs 열기", command=lambda: os.startfile("logs")).pack(fill="x")

    def _append(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def _refresh_attachment_label(self):
        if not self.attached_files:
            self.attach_label.config(text="첨부 없음")
        else:
            self.attach_label.config(text=f"{len(self.attached_files)}개 첨부")

    def attach_files(self):
        paths = filedialog.askopenfilenames()

        if not paths:
            return

        for path in paths:
            if not os.path.isfile(path):
                continue
            if os.path.getsize(path) <= 0:
                continue
            if path not in self.attached_files:
                self.attached_files.append(path)

        self._refresh_attachment_label()

    def clear_files(self):
        self.attached_files = []
        self._refresh_attachment_label()

    def handle_input(self):
        text = self.entry.get().strip()

        if not text:
            return

        if not self.attached_files:
            messagebox.showwarning("첨부 필요", "첨부 파일이 없습니다.")
            return

        self._append(f"[YOU] {text}")

        for f in self.attached_files:
            self._append(f"[ATTACH] {f}")

        self.entry.delete(0, "end")

        self.run_task(text)

    def run_task(self, command):
        def worker():
            self.current_task_var.set("running")

            if any(k in command for k in ["만들어줘", "개발", "프로그램", "게임"]):
                self._append("[MANGO] 시방서 생성 필요")
                path = os.path.join("workspace", "spec.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(command)
                self._append(f"[MANGO] 시방서 생성됨: {path}")
                self.current_task_var.set("done")
                return

            self._append("[MANGO] 작업 실행 완료")
            self.current_task_var.set("done")

        threading.Thread(target=worker, daemon=True).start()

    def loop_on(self):
        self.running = True
        self._append("[MANGO] 루프 ON")

    def loop_off(self):
        self.running = False
        self._append("[MANGO] 루프 OFF")

    def run_loop(self):
        command = self.entry.get().strip()

        if not command:
            messagebox.showwarning("입력 필요", "목표 입력 필요")
            return

        if not self.attached_files:
            messagebox.showwarning("첨부 필요", "첨부 파일 필요")
            return

        def loop():
            self.current_task_var.set("running")
            while self.running:
                self._append(f"[LOOP] {command}")
                break
            self.current_task_var.set("done")

        threading.Thread(target=loop, daemon=True).start()


def run():
    root = tk.Tk()
    app = MangoApp(root)
    root.mainloop()
