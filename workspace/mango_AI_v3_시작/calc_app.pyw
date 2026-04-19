import tkinter as tk
from tkinter import messagebox


class CalculatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Tkinter Calculator")
        self.root.geometry("360x520")
        self.root.minsize(320, 460)
        self.root.configure(bg="#1f2430")

        self.expression = ""
        self.display_var = tk.StringVar(value="0")

        self._build_ui()

    def _build_ui(self) -> None:
        display_frame = tk.Frame(self.root, bg="#1f2430", padx=16, pady=20)
        display_frame.pack(fill="both")

        display = tk.Entry(
            display_frame,
            textvariable=self.display_var,
            font=("Consolas", 28),
            justify="right",
            bd=0,
            relief="flat",
            bg="#2a3142",
            fg="#f5f7fa",
            insertbackground="#f5f7fa",
        )
        display.pack(fill="both", ipady=20)

        buttons_frame = tk.Frame(self.root, bg="#1f2430", padx=16, pady=8)
        buttons_frame.pack(expand=True, fill="both")

        layout = [
            ["C", "⌫", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["+/-", "0", ".", "="],
        ]

        for row_index, row in enumerate(layout):
            buttons_frame.rowconfigure(row_index, weight=1)
            for col_index, label in enumerate(row):
                buttons_frame.columnconfigure(col_index, weight=1)
                button = tk.Button(
                    buttons_frame,
                    text=label,
                    font=("Segoe UI", 18, "bold"),
                    bd=0,
                    relief="flat",
                    command=lambda value=label: self._on_button_click(value),
                    bg=self._button_bg(label),
                    fg=self._button_fg(label),
                    activebackground="#596780",
                    activeforeground="#ffffff",
                    cursor="hand2",
                )
                button.grid(
                    row=row_index,
                    column=col_index,
                    sticky="nsew",
                    padx=6,
                    pady=6,
                    ipadx=6,
                    ipady=16,
                )

        self.root.bind("<Return>", lambda _event: self._calculate())
        self.root.bind("<BackSpace>", lambda _event: self._backspace())
        self.root.bind("<Escape>", lambda _event: self._clear())

    def _button_bg(self, label: str) -> str:
        if label == "=":
            return "#ff9f1c"
        if label in {"/", "*", "-", "+", "%", "C", "⌫", "+/-"}:
            return "#3c4458"
        return "#2a3142"

    def _button_fg(self, label: str) -> str:
        if label == "=":
            return "#1f2430"
        return "#f5f7fa"

    def _on_button_click(self, value: str) -> None:
        if value == "C":
            self._clear()
        elif value == "⌫":
            self._backspace()
        elif value == "=":
            self._calculate()
        elif value == "+/-":
            self._toggle_sign()
        else:
            self._append(value)

    def _append(self, value: str) -> None:
        if self.display_var.get() == "Error":
            self._clear()

        if value in "+-*/%" and (not self.expression or self.expression[-1] in "+-*/%"):
            return

        if value == ".":
            current_number = self._current_number()
            if "." in current_number:
                return
            if not current_number:
                value = "0."

        self.expression += value
        self.display_var.set(self.expression or "0")

    def _current_number(self) -> str:
        parts = []
        for char in reversed(self.expression):
            if char in "+-*/%":
                break
            parts.append(char)
        return "".join(reversed(parts))

    def _clear(self) -> None:
        self.expression = ""
        self.display_var.set("0")

    def _backspace(self) -> None:
        if self.display_var.get() == "Error":
            self._clear()
            return

        self.expression = self.expression[:-1]
        self.display_var.set(self.expression or "0")

    def _toggle_sign(self) -> None:
        if not self.expression or self.display_var.get() == "Error":
            return

        operator_index = -1
        for index in range(len(self.expression) - 1, -1, -1):
            if self.expression[index] in "+-*/%":
                operator_index = index
                break

        current_number = self.expression[operator_index + 1 :]
        if not current_number:
            return

        prefix = self.expression[: operator_index + 1]
        if current_number.startswith("-"):
            current_number = current_number[1:]
        else:
            current_number = f"-{current_number}"

        self.expression = prefix + current_number
        self.display_var.set(self.expression)

    def _calculate(self) -> None:
        if not self.expression:
            return

        if self.expression[-1] in "+-*/%":
            return

        try:
            # Limit evaluation to arithmetic symbols assembled by button presses.
            result = eval(self.expression, {"__builtins__": {}}, {})
        except ZeroDivisionError:
            messagebox.showerror("Calculation Error", "0으로 나눌 수 없습니다.")
            self.expression = ""
            self.display_var.set("Error")
            return
        except Exception:
            messagebox.showerror("Calculation Error", "계산식을 처리할 수 없습니다.")
            self.expression = ""
            self.display_var.set("Error")
            return

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        self.expression = str(result)
        self.display_var.set(self.expression)


def main() -> None:
    root = tk.Tk()
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
