import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox


class NotepadApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Simple Notepad")
        self.root.geometry("900x620")
        self.root.minsize(640, 420)
        self.root.configure(bg="#f3efe7")

        self.current_file: Path | None = None
        self.is_dirty = False

        self.status_var = tk.StringVar(value="Untitled")

        self._build_ui()
        self._bind_events()
        self._update_title()

    def _build_ui(self) -> None:
        self.root.option_add("*Font", ("Consolas", 11))

        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close, accelerator="Ctrl+Q")
        menu_bar.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menu_bar)

        toolbar = tk.Frame(self.root, bg="#e7dfd1", padx=14, pady=10)
        toolbar.pack(fill="x")

        open_button = tk.Button(
            toolbar,
            text="Load File",
            command=self.open_file,
            padx=14,
            pady=6,
            bd=0,
            relief="flat",
            bg="#c9b089",
            fg="#1f1f1f",
            activebackground="#b99f75",
            activeforeground="#1f1f1f",
        )
        open_button.pack(side="left")

        self.file_label_var = tk.StringVar(value="No file loaded")
        file_label = tk.Label(
            toolbar,
            textvariable=self.file_label_var,
            anchor="w",
            bg="#e7dfd1",
            fg="#4f4538",
            padx=12,
        )
        file_label.pack(side="left", fill="x", expand=True)

        editor_frame = tk.Frame(self.root, bg="#f3efe7", padx=14, pady=14)
        editor_frame.pack(expand=True, fill="both")

        self.text = tk.Text(
            editor_frame,
            wrap="word",
            undo=True,
            bd=0,
            relief="flat",
            padx=16,
            pady=16,
            bg="#fffdf8",
            fg="#1f1f1f",
            insertbackground="#1f1f1f",
            selectbackground="#d9c7a5",
            selectforeground="#1f1f1f",
        )

        scrollbar = tk.Scrollbar(editor_frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)

        self.text.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            padx=12,
            pady=8,
            bg="#ded6c8",
            fg="#3a342b",
        )
        status_bar.pack(fill="x")

    def _bind_events(self) -> None:
        self.root.bind("<Control-n>", lambda _event: self.new_file())
        self.root.bind("<Control-o>", lambda _event: self.open_file())
        self.root.bind("<Control-s>", lambda _event: self.save_file())
        self.root.bind("<Control-S>", lambda _event: self.save_file_as())
        self.root.bind("<Control-q>", lambda _event: self.on_close())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.text.bind("<<Modified>>", self._on_modified)

    def _on_modified(self, _event: tk.Event) -> None:
        if self.text.edit_modified():
            self.is_dirty = True
            self._update_title()
            self._update_status()
            self.text.edit_modified(False)

    def _update_title(self) -> None:
        file_name = self.current_file.name if self.current_file else "Untitled"
        dirty_marker = " *" if self.is_dirty else ""
        self.root.title(f"{file_name}{dirty_marker} - Simple Notepad")

    def _update_status(self) -> None:
        if self.current_file:
            prefix = str(self.current_file)
            self.file_label_var.set(f"Loaded file: {self.current_file.name}")
        else:
            prefix = "Untitled"
            self.file_label_var.set("No file loaded")

        if self.is_dirty:
            prefix += " | Unsaved changes"

        self.status_var.set(prefix)

    def _set_text_content(self, content: str) -> None:
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.is_dirty = False
        self._update_title()
        self._update_status()

    def _confirm_discard_changes(self) -> bool:
        if not self.is_dirty:
            return True

        return messagebox.askyesno(
            "Unsaved Changes",
            "There are unsaved changes. Continue and discard them?",
        )

    def new_file(self) -> None:
        if not self._confirm_discard_changes():
            return

        self.current_file = None
        self._set_text_content("")

    def open_file(self) -> None:
        if not self._confirm_discard_changes():
            return

        selected = filedialog.askopenfilename(
            title="Open Text File",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("Markdown Files", "*.md"),
                ("All Files", "*.*"),
            ],
        )
        if not selected:
            return

        path = Path(selected)
        content = self._read_text_file(path)
        if content is None:
            return

        self.current_file = path
        self._set_text_content(content)

    def save_file(self) -> bool:
        if self.current_file is None:
            return self.save_file_as()

        return self._write_to_path(self.current_file)

    def save_file_as(self) -> bool:
        selected = filedialog.asksaveasfilename(
            title="Save Text File",
            defaultextension=".txt",
            initialfile=self.current_file.name if self.current_file else "untitled.txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Markdown Files", "*.md"),
                ("Python Files", "*.py"),
                ("All Files", "*.*"),
            ],
        )
        if not selected:
            return False

        path = Path(selected)
        self.current_file = path
        return self._write_to_path(path)

    def _write_to_path(self, path: Path) -> bool:
        try:
            path.write_text(self.text.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save Failed", f"Could not save the file.\n\n{exc}")
            return False

        self.is_dirty = False
        self._update_title()
        self._update_status()
        return True

    def _read_text_file(self, path: Path) -> str | None:
        for encoding in ("utf-8", "utf-8-sig", "cp949"):
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except OSError as exc:
                messagebox.showerror("Open Failed", f"Could not open the file.\n\n{exc}")
                return None

        messagebox.showerror(
            "Open Failed",
            "Only UTF-8 or CP949 text files can be loaded.",
        )
        return None

    def on_close(self) -> None:
        if self.is_dirty:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Save changes before closing?",
            )
            if result is None:
                return
            if result and not self.save_file():
                return

        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = NotepadApp(root)
    app._set_text_content(
        "Simple Notepad\n\n"
        "Use File > Save or Ctrl+S to store your notes as a text file."
    )
    root.mainloop()


if __name__ == "__main__":
    main()
