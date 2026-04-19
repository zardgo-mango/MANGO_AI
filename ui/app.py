import os
import sys
import threading
import tkinter as tk
from tkinter import Toplevel, filedialog
from tkinter import ttk

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from intent_engine import detect_intent
from core import runtime as core

BG = "#EAE7DC"
PANEL = "#F7F7F7"
ACCENT = "#2F6FB2"
TEXT = "#111111"


class SettingsWindow:
    def __init__(self, parent, current_settings, apply_callback):
        self.apply_callback = apply_callback
        self.win = Toplevel(parent)
        self.win.title("설정")
        self.win.geometry("420x360")
        self.win.minsize(380, 320)
        self.win.resizable(True, True)

        container = tk.Frame(self.win, padx=16, pady=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)

        labels = [
            ("채팅 글씨 크기", "chat_font_size", 10, 24),
            ("상태창 글씨 크기", "status_font_size", 10, 20),
            ("입력창 글씨 크기", "input_font_size", 10, 22),
            ("줄 간격", "line_spacing", 4, 28),
        ]
        self.scales = {}
        row = 0
        for label, key, lo, hi in labels:
            tk.Label(container, text=label, font=("Malgun Gothic", 11)).grid(row=row, column=0, sticky="w")
            row += 1
            scale = tk.Scale(container, from_=lo, to=hi, orient="horizontal")
            scale.set(current_settings[key])
            scale.grid(row=row, column=0, sticky="ew", pady=(0, 10))
            self.scales[key] = scale
            row += 1

        btn_wrap = tk.Frame(container)
        btn_wrap.grid(row=row, column=0, sticky="e")
        tk.Button(btn_wrap, text="취소", command=self.win.destroy, font=("Malgun Gothic", 11), width=10).pack(side="left", padx=(0, 8))
        tk.Button(btn_wrap, text="저장", command=self.save, font=("Malgun Gothic", 11, "bold"), width=10).pack(side="left")

    def save(self):
        settings = {k: int(v.get()) for k, v in self.scales.items()}
        self.apply_callback(settings)
        self.win.destroy()


class MangoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MANGO_v24_fix3")
        self.root.geometry("1220x760")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)

        self.settings = core.load_settings()
        self.attached_files = []
        self.avatar_photo = None
        self._build_ui()
        self.apply_settings(self.settings)
        self._refresh_status()
        self._poll_status()

        self._append("[MANGO] MANGO_v24_fix3 READY")
        self._append("")
        self._append("[MANGO] 현재 실행 폴더 기준 workspace/logs/data 사용")
        self._append("[MANGO] GUI 결과물은 .pyw 실행 권장")
        self._append("[MANGO] 첨부파일은 작업 자산으로 복사되어 실제 UI 반영에 사용됩니다")
        self._append("")

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        top = tk.Frame(self.root, bg=BG, padx=14, pady=10)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        self.canvas = tk.Canvas(top, width=140, height=140, bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nw")
        self._draw_avatar()

        title_wrap = tk.Frame(top, bg=BG)
        title_wrap.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        title_top = tk.Frame(title_wrap, bg=BG)
        title_top.pack(fill="x", pady=(8, 0))
        tk.Label(title_top, text="MANGO_v24_fix3", bg=BG, fg="#000", font=("Malgun Gothic", 24, "bold")).pack(side="left")
        tk.Button(title_top, text="설정", command=self.open_settings, font=("Malgun Gothic", 10, "bold"), width=8).pack(side="right")

        tk.Label(title_wrap, text="작업 진행 중", bg=BG, fg=ACCENT, font=("Malgun Gothic", 15, "bold")).pack(anchor="w", pady=(8, 6))
        tk.Label(title_wrap, text="현재 실행 폴더 기준 경로 고정", bg=BG, fg=TEXT, font=("Malgun Gothic", 13)).pack(anchor="w")

        progress_wrap = tk.Frame(title_wrap, bg=BG)
        progress_wrap.pack(fill="x", pady=(10, 0))
        self.progress_var = tk.IntVar(value=0)
        self.stage_var = tk.StringVar(value="ready")
        self.current_task_var = tk.StringVar(value="대기 중")
        tk.Label(progress_wrap, textvariable=self.stage_var, bg=BG, fg=TEXT, font=("Malgun Gothic", 11, "bold")).pack(anchor="w")
        self.progress = ttk.Progressbar(progress_wrap, maximum=100, variable=self.progress_var)
        self.progress.pack(fill="x", pady=(4, 4))
        tk.Label(progress_wrap, textvariable=self.current_task_var, bg=BG, fg="#444", font=("Malgun Gothic", 10)).pack(anchor="w")

        main = tk.Frame(self.root, bg=BG, padx=14, pady=6)
        main.grid(row=1, column=0, sticky="nsew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=5)
        main.grid_columnconfigure(1, weight=3)

        left = tk.Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = tk.Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        box_left = tk.Frame(left, bg=PANEL, bd=1, relief="solid")
        box_left.grid(row=0, column=0, sticky="nsew")
        box_left.grid_rowconfigure(1, weight=1)
        box_left.grid_columnconfigure(0, weight=1)

        tk.Label(box_left, text="대화 / 보고", bg=PANEL, fg=TEXT, font=("Malgun Gothic", 17, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        text_frame = tk.Frame(box_left, bg=PANEL)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(text_frame, wrap="word", bg="white", fg=TEXT, padx=12, pady=12)
        self.text.grid(row=0, column=0, sticky="nsew")
        text_scroll = tk.Scrollbar(text_frame, command=self.text.yview)
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=text_scroll.set, state="disabled")

        input_wrap = tk.Frame(box_left, bg=PANEL)
        input_wrap.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        input_wrap.grid_columnconfigure(0, weight=1)

        self.entry = tk.Entry(input_wrap)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=7)
        self.entry.bind("<Return>", self._on_enter)
        tk.Button(input_wrap, text="보내기", command=self.handle_input, font=("Malgun Gothic", 11, "bold"), width=9).grid(row=0, column=1)

        attach_row = tk.Frame(input_wrap, bg=PANEL)
        attach_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        attach_row.grid_columnconfigure(0, weight=1)
        self.attach_label = tk.Label(
            attach_row,
            text="첨부 없음 | 파일 첨부 버튼 사용",
            bg="#FFF6D8",
            fg="#5E4B00",
            anchor="w",
            padx=10,
            pady=8,
            relief="solid",
            bd=1,
        )
        self.attach_label.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.attach_label.bind("<Button-1>", lambda e: self.attach_files())
        tk.Button(attach_row, text="파일 첨부", command=self.attach_files, font=("Malgun Gothic", 10, "bold"), width=10).grid(row=0, column=1, padx=(0, 4))
        tk.Button(attach_row, text="첨부 비움", command=self.clear_attachments, font=("Malgun Gothic", 10), width=10).grid(row=0, column=2)

        box_right = tk.Frame(right, bg=PANEL, bd=1, relief="solid")
        box_right.grid(row=0, column=0, sticky="nsew")
        box_right.grid_rowconfigure(1, weight=1)
        box_right.grid_columnconfigure(0, weight=1)

        tk.Label(box_right, text="상태 / 제어", bg=PANEL, fg=TEXT, font=("Malgun Gothic", 17, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        status_frame = tk.Frame(box_right, bg=PANEL)
        status_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        status_frame.grid_rowconfigure(0, weight=1)
        status_frame.grid_columnconfigure(0, weight=1)

        self.status_text = tk.Text(status_frame, wrap="word", bg="white", fg=TEXT, padx=12, pady=12)
        self.status_text.grid(row=0, column=0, sticky="nsew")
        status_scroll = tk.Scrollbar(status_frame, command=self.status_text.yview)
        status_scroll.grid(row=0, column=1, sticky="ns")
        self.status_text.configure(yscrollcommand=status_scroll.set, state="disabled")

        button_area = tk.Frame(box_right, bg=PANEL)
        button_area.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        button_area.grid_columnconfigure(0, weight=1)

        buttons = [
            ("프로젝트 보고", lambda: self._system_append(core.report())),
            ("기억 보기", lambda: self._system_append(core.get_memory_report())),
            ("루프 ON", lambda: self._system_append(core.enable_auto_loop())),
            ("루프 OFF", lambda: self._system_append(core.disable_auto_loop())),
            ("루프 상태", lambda: self._system_append(core.auto_loop_status())),
            ("자동 루프 실행", self._run_auto_loop_from_entry),
            ("workspace 열기", self.open_workspace_folder),
            ("logs 열기", self.open_logs_folder),
            ("에러로그 보기", self.show_launch_error),
            ("temp 정리", lambda: self._system_append(core.cleanup_temp())),
        ]
        for idx, (label, command) in enumerate(buttons):
            tk.Button(button_area, text=label, command=command, font=("Malgun Gothic", 11), height=1).grid(row=idx, column=0, sticky="ew", pady=3)

    def _set_busy(self, is_busy: bool, task_text: str = ""):
        self.current_task_var.set(task_text or ("작업 중" if is_busy else "대기 중"))
        state = "disabled" if is_busy else "normal"
        try:
            self.entry.configure(state=state)
        except Exception:
            pass

    def attach_files(self):
        paths = filedialog.askopenfilenames(title="MANGO 첨부파일 선택")
        if not paths:
            return
        for path in paths:
            if path not in self.attached_files:
                self.attached_files.append(path)
        self._refresh_attachment_label()
        self._append("")
        self._append("[MANGO] 첨부파일 추가")
        for path in paths:
            self._append(f"- {path}")

    def clear_attachments(self):
        self.attached_files = []
        self._refresh_attachment_label()

    def _refresh_attachment_label(self):
        if not self.attached_files:
            self.attach_label.configure(text="첨부 없음 | 파일 첨부 버튼 사용")
            return
        preview = " | ".join(os.path.basename(x) for x in self.attached_files[:3])
        if len(self.attached_files) > 3:
            preview += f" 외 {len(self.attached_files)-3}개"
        self.attach_label.configure(text=f"첨부됨: {preview}")

    def _build_prompt_with_attachments(self, user_input: str):
        if not self.attached_files:
            return user_input
        attachment_lines = ["[첨부파일]"] + [f"- {path}" for path in self.attached_files]
        return user_input + "\n\n" + "\n".join(attachment_lines)

    def _run_core_action(self, user_input: str):
        prompt_text = self._build_prompt_with_attachments(user_input)

        def worker():
            try:
                intent = detect_intent(user_input)
                if any(k in user_input for k in ["기억해", "메모해"]):
                    result = core.remember(prompt_text)
                elif intent == "project":
                    result = core.start_project(prompt_text)
                elif intent == "outsource":
                    result = core.make_outsource_prompt(prompt_text)
                elif intent == "codex":
                    result = core.auto_codex_execute(prompt_text)
                elif intent == "report":
                    result = core.report()
                elif intent == "memory":
                    result = core.get_memory_report()
                elif intent == "auto_loop":
                    result = core.start_auto_loop(prompt_text)
                else:
                    result = core.chat(prompt_text)
            except Exception as e:
                result = f"[MANGO] 작업 중 오류 발생\n\n{e}"
            self.root.after(0, lambda: self._finish_background_result(result))

        self._set_busy(True, user_input[:80])
        threading.Thread(target=worker, daemon=True).start()

    def _finish_background_result(self, result: str):
        self._append("")
        self._append(result)
        self._refresh_status()
        self._set_busy(False, "대기 중")
        self.clear_attachments()

    def _run_auto_loop_from_entry(self):
        goal = self.entry.get().strip()
        if not goal:
            goal = "파이썬 tkinter 계산기 프로그램 만들어서 calc_app.py로 저장해"
        self._append("")
        self._append(f"[YOU] {goal}")
        self.entry.delete(0, "end")
        self._run_core_action(goal)

    def open_settings(self):
        SettingsWindow(self.root, self.settings, self.apply_settings_and_save)

    def apply_settings_and_save(self, settings):
        self.settings = settings
        core.save_settings(settings)
        self.apply_settings(settings)
        self._append("")
        self._append("[MANGO] 설정 저장 완료")

    def apply_settings(self, settings):
        self.text.configure(font=("Consolas", settings["chat_font_size"]), spacing1=4, spacing2=6, spacing3=settings["line_spacing"])
        self.status_text.configure(font=("Consolas", settings["status_font_size"]), spacing1=2, spacing2=3, spacing3=max(5, settings["line_spacing"] - 3))
        self.entry.configure(font=("Malgun Gothic", settings["input_font_size"]))

    def _draw_avatar(self):
        self.canvas.delete("all")
        avatar_path = core.get_paths_report().get("avatar_image")
        if avatar_path and os.path.exists(avatar_path) and Image and ImageTk:
            try:
                image = Image.open(avatar_path).convert("RGBA")
                image.thumbnail((128, 128))
                self.avatar_photo = ImageTk.PhotoImage(image)
                self.canvas.create_image(70, 68, image=self.avatar_photo)
                self.canvas.create_text(70, 132, text="MANGO", font=("Malgun Gothic", 11, "bold"))
                return
            except Exception:
                self.avatar_photo = None
        self.canvas.create_oval(18, 14, 122, 118, fill="#F1CF6A", outline="#9B7C00", width=2)
        self.canvas.create_oval(42, 44, 54, 56, fill="black")
        self.canvas.create_oval(86, 44, 98, 56, fill="black")
        self.canvas.create_arc(40, 62, 100, 96, start=200, extent=140, style="arc", width=3)
        self.canvas.create_text(70, 130, text="MANGO", font=("Malgun Gothic", 11, "bold"))

    def _append(self, msg):
        self.text.configure(state="normal")
        self.text.insert("end", msg + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def _system_append(self, msg):
        self._append("")
        self._append(msg)
        self._refresh_status()

    def _refresh_status(self):
        state = core.load_state()
        paths = core.get_paths_report()
        self.progress_var.set(int(state.get("progress", 0)))
        self.stage_var.set(f"상태: {state.get('stage')}")
        self.current_task_var.set((state.get("last_result") or "대기 중")[:80])
        lines = [
            f"root: {paths.get('root')}",
            f"workspace_root: {paths.get('workspace_root')}",
            f"project_workspace: {paths.get('project_workspace')}",
            f"logs: {paths.get('logs')}",
            f"data: {paths.get('data')}",
            f"assets: {paths.get('assets')}",
            f"codex: {state.get('codex_mode', '실제 Codex CLI')}",
            f"codex_path: {state.get('codex_path') or '(없음)'}",
            f"node_path: {state.get('node_path') or '(없음)'}",
            f"project: {state.get('project_name') or '없음'}",
            f"stage: {state.get('stage')}",
            f"progress: {state.get('progress', 0)}%",
            f"auto_loop: {state.get('auto_loop_enabled')}",
            f"last_files: {', '.join(state.get('last_created_files', [])) or '(없음)'}",
            f"log_summary: {state.get('last_log_summary') or '(없음)'}",
            f"launch_error: {core.get_last_launch_error_report()}",
        ]
        self.status_text.configure(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("end", "\n".join(lines))
        self.status_text.configure(state="disabled")

    def open_workspace_folder(self):
        self._open_folder(core.get_paths_report().get("project_workspace"))

    def open_logs_folder(self):
        self._open_folder(core.get_paths_report().get("logs"))

    def _open_folder(self, path):
        try:
            if os.name == "nt":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
            self._append("")
            self._append(f"[MANGO] 폴더 열기\n{path}")
        except Exception as e:
            self._append("")
            self._append(f"[MANGO] 폴더 열기 실패\n{e}")

    def show_launch_error(self):
        self._system_append("[MANGO] 최근 GUI 실행 오류\n\n" + core.get_last_launch_error_report())

    def _on_enter(self, event):
        self.handle_input()

    def handle_input(self):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self._append("")
        self._append(f"[YOU] {user_input}")
        if self.attached_files:
            for path in self.attached_files:
                self._append(f"[ATTACH] {path}")
        self.entry.delete(0, "end")
        self._run_core_action(user_input)

    def _poll_status(self):
        self._refresh_status()
        self.root.after(1200, self._poll_status)

    def run(self):
        self.root.mainloop()
