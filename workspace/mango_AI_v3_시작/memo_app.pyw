import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


class MemoApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Simple Memo")
        self.root.geometry("900x600")

        self.current_file: Path | None = None
        self.is_modified = False

        self._build_menu()
        self._build_editor()
        self._bind_shortcuts()
        self._update_title()

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)

        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

    def _build_editor(self) -> None:
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True)

        self.text = tk.Text(frame, undo=True, wrap="word", font=("Consolas", 12))
        scrollbar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            padx=8,
            pady=4,
            relief="sunken",
        )
        status_bar.pack(fill="x", side="bottom")

        self.text.edit_modified(False)
        self.text.bind("<<Modified>>", self._on_modified)

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-n>", lambda event: self.new_file())
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-S>", lambda event: self.save_file_as())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_modified(self, _event=None) -> None:
        if self.text.edit_modified():
            self.is_modified = True
            self._update_title()
            self._update_status("Edited")
            self.text.edit_modified(False)

    def _is_dirty(self) -> bool:
        return self.is_modified

    def _update_title(self) -> None:
        name = self.current_file.name if self.current_file else "Untitled"
        dirty_prefix = "* " if self.is_modified else ""
        self.root.title(f"{dirty_prefix}{name} - Simple Memo")

    def _update_status(self, message: str) -> None:
        self.status_var.set(message)

    def _confirm_discard_changes(self) -> bool:
        if not self._is_dirty():
            return True

        answer = messagebox.askyesnocancel(
            "Unsaved Changes",
            "Save changes before continuing?",
        )
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def new_file(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.text.delete("1.0", "end")
        self.current_file = None
        self.is_modified = False
        self.text.edit_modified(False)
        self._update_title()
        self._update_status("New file")

    def open_file(self) -> None:
        if not self._confirm_discard_changes():
            return

        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        path = Path(file_path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding="cp949")
            except OSError as exc:
                messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")
                return
        except OSError as exc:
            messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.current_file = path
        self.is_modified = False
        self.text.edit_modified(False)
        self._update_title()
        self._update_status(f"Opened: {path.name}")

    def save_file(self) -> bool:
        if self.current_file is None:
            return self.save_file_as()
        return self._write_to_path(self.current_file)

    def save_file_as(self) -> bool:
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Python Files", "*.py"), ("All Files", "*.*")],
        )
        if not file_path:
            return False
        self.current_file = Path(file_path)
        return self._write_to_path(self.current_file)

    def _write_to_path(self, path: Path) -> bool:
        content = self.text.get("1.0", "end-1c")
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Could not save file:\n{exc}")
            return False

        self.is_modified = False
        self.text.edit_modified(False)
        self._update_title()
        self._update_status(f"Saved: {path.name}")
        return True

    def on_close(self) -> None:
        if self._confirm_discard_changes():
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    MemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
