from __future__ import annotations

import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
NOTE_PATH = BASE_DIR / "망고2호기_메모.txt"
IMAGE_CANDIDATES = [
    BASE_DIR / "assets" / "MANGO_1호기.jpg",
    BASE_DIR / "assets" / "MANGO_1호기_1.jpg",
    BASE_DIR / "assets" / "MANGO_1호기_2.jpg",
    BASE_DIR / "assets" / "MANGO_1호기_3.jpg",
    Path(r"G:\내 드라이브\MANGO_SHARED\MANGO 1호기.jpg"),
]

HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>망고2호기 메모장</title>
  <link rel="icon" href="/image">
  <style>
    :root {
      --bg-1: #fff4cf;
      --bg-2: #ffd267;
      --panel: rgba(255, 252, 245, 0.88);
      --line: rgba(92, 67, 15, 0.14);
      --ink: #4e3402;
      --accent: #ff9f1c;
      --accent-strong: #e87400;
      --shadow: 0 18px 45px rgba(110, 72, 0, 0.16);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
      color: var(--ink);
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.95), transparent 32%),
        radial-gradient(circle at right 18%, rgba(255,237,170,0.85), transparent 24%),
        linear-gradient(135deg, var(--bg-1), var(--bg-2));
    }

    .shell {
      width: min(1100px, calc(100vw - 32px));
      margin: 24px auto;
      display: grid;
      gap: 18px;
    }

    .hero {
      display: grid;
      grid-template-columns: 128px 1fr;
      gap: 18px;
      align-items: center;
      padding: 18px 20px;
      border-radius: 26px;
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.6);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .hero img {
      width: 128px;
      height: 128px;
      object-fit: cover;
      border-radius: 28px;
      background: #fff;
      border: 4px solid rgba(255,255,255,0.75);
      box-shadow: 0 10px 24px rgba(120, 82, 2, 0.18);
    }

    .title {
      margin: 0 0 8px;
      font-size: clamp(28px, 3vw, 42px);
      line-height: 1.1;
      letter-spacing: -0.03em;
    }

    .subtitle {
      margin: 0;
      font-size: 15px;
      opacity: 0.82;
    }

    .workspace {
      display: grid;
      gap: 14px;
      padding: 18px;
      border-radius: 26px;
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.6);
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 11px 16px;
      font-size: 14px;
      font-weight: 700;
      color: white;
      background: linear-gradient(135deg, var(--accent), var(--accent-strong));
      cursor: pointer;
      box-shadow: 0 8px 18px rgba(232, 116, 0, 0.25);
      transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 24px rgba(232, 116, 0, 0.28);
    }

    .status {
      margin-left: auto;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      background: rgba(255, 247, 225, 0.95);
      border: 1px solid var(--line);
    }

    textarea {
      width: 100%;
      min-height: 62vh;
      padding: 20px 22px;
      resize: vertical;
      border-radius: 22px;
      border: 1px solid var(--line);
      background:
        linear-gradient(to bottom, rgba(255,255,255,0.96), rgba(255,250,240,0.94)),
        repeating-linear-gradient(
          to bottom,
          transparent 0,
          transparent 33px,
          rgba(239, 190, 70, 0.11) 33px,
          rgba(239, 190, 70, 0.11) 34px
        );
      color: var(--ink);
      font-size: 17px;
      line-height: 34px;
      outline: none;
      box-shadow: inset 0 1px 2px rgba(0,0,0,0.03);
    }

    .meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 13px;
      opacity: 0.78;
    }

    @media (max-width: 720px) {
      .hero {
        grid-template-columns: 1fr;
        text-align: center;
      }

      .hero img {
        margin: 0 auto;
      }

      .status {
        width: 100%;
        margin-left: 0;
        text-align: center;
      }

      textarea {
        min-height: 56vh;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <img src="/image" alt="망고 1호기 이미지">
      <div>
        <h1 class="title">망고2호기 메모장</h1>
        <p class="subtitle">첨부한 망고 이미지를 실제 헤더에 넣은 간단한 로컬 메모장입니다.</p>
      </div>
    </section>

    <section class="workspace">
      <div class="toolbar">
        <button id="saveButton" type="button">저장</button>
        <button id="clearButton" type="button">새 메모</button>
        <button id="reloadButton" type="button">불러오기</button>
        <div class="status" id="statusText">준비됨</div>
      </div>
      <textarea id="editor" placeholder="여기에 메모를 입력하세요. Ctrl+S로도 저장됩니다."></textarea>
      <div class="meta">
        <span id="filePath">저장 파일: 망고2호기_메모.txt</span>
        <span id="counter">0자</span>
      </div>
    </section>
  </main>

  <script>
    const editor = document.getElementById("editor");
    const counter = document.getElementById("counter");
    const statusText = document.getElementById("statusText");

    function setStatus(message) {
      statusText.textContent = message;
    }

    function updateCounter() {
      counter.textContent = `${editor.value.length}자`;
    }

    async function loadNote() {
      setStatus("불러오는 중...");
      const response = await fetch("/note");
      const data = await response.json();
      editor.value = data.content || "";
      updateCounter();
      setStatus("불러오기 완료");
    }

    async function saveNote() {
      setStatus("저장하는 중...");
      const response = await fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editor.value })
      });
      const data = await response.json();
      setStatus(data.message || "저장 완료");
    }

    document.getElementById("saveButton").addEventListener("click", saveNote);
    document.getElementById("reloadButton").addEventListener("click", loadNote);
    document.getElementById("clearButton").addEventListener("click", () => {
      editor.value = "";
      updateCounter();
      setStatus("새 메모 시작");
      editor.focus();
    });

    editor.addEventListener("input", updateCounter);
    window.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveNote();
      }
    });

    window.addEventListener("load", loadNote);
  </script>
</body>
</html>
"""


def resolve_image_path() -> Path | None:
    for candidate in IMAGE_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


class MangoMemoHandler(BaseHTTPRequestHandler):
    def _send_bytes(self, content: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(content, "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_bytes(HTML.encode("utf-8"), "text/html; charset=utf-8")
            return

        if parsed.path == "/note":
            content = NOTE_PATH.read_text(encoding="utf-8") if NOTE_PATH.exists() else ""
            self._send_json({"content": content})
            return

        if parsed.path == "/image":
            image_path = resolve_image_path()
            if image_path is None:
                self._send_json({"message": "이미지를 찾을 수 없습니다."}, HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(image_path.read_bytes(), "image/jpeg")
            return

        self._send_json({"message": "Not Found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/save":
            self._send_json({"message": "Not Found"}, HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw_body.decode("utf-8"))
        content = payload.get("content", "")
        NOTE_PATH.write_text(content, encoding="utf-8")
        self._send_json({"message": "저장 완료: 망고2호기_메모.txt"})

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    image_path = resolve_image_path()
    if image_path is None:
        print("이미지를 찾지 못했습니다. 'assets/MANGO_1호기.jpg' 또는 공유 경로를 확인하세요.")

    server = ThreadingHTTPServer(("127.0.0.1", 0), MangoMemoHandler)
    host, port = server.server_address
    url = f"http://{host}:{port}/"

    print("망고2호기 메모장을 실행합니다.")
    print(f"브라우저가 열리지 않으면 이 주소를 여세요: {url}")

    timer = threading.Timer(0.6, lambda: webbrowser.open(url))
    timer.daemon = True
    timer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
