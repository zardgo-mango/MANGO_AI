import threading
import time


class LoopManager:
    def __init__(self, ui_callback):
        self.running = False
        self.thread = None
        self.ui_callback = ui_callback
        self.current_task = None

    def start(self, task_func, command):
        if self.running:
            return

        self.running = True
        self.current_task = command

        self.thread = threading.Thread(
            target=self._run_loop,
            args=(task_func, command),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.running = False

    def _run_loop(self, task_func, command):
        self.ui_callback("running", command)

        try:
            while self.running:
                result = task_func(command)

                if result == "DONE":
                    self.ui_callback("done", command)
                    break

                time.sleep(1)

        except Exception as e:
            self.ui_callback("error", str(e))
        finally:
            self.running = False
