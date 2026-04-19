import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, "workspace")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive")
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
DATA_DIR = os.path.join(ROOT_DIR, "data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

for d in [WORKSPACE_DIR, ARCHIVE_DIR, TEMP_DIR, LOG_DIR, DATA_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)

STATE_FILE = os.path.join(DATA_DIR, "state.json")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
TASKS_FILE = os.path.join(DATA_DIR, "tasks.json")

LAST_STDOUT = os.path.join(LOG_DIR, "codex_last_stdout.txt")
LAST_STDERR = os.path.join(LOG_DIR, "codex_last_stderr.txt")
LAST_SUMMARY = os.path.join(LOG_DIR, "codex_last_summary.txt")
LAST_RUNTIME = os.path.join(LOG_DIR, "runtime_error.txt")
LAST_GUI_ERROR = os.path.join(LOG_DIR, "generated_app_last_error.txt")
AUTO_LOOP_LOG = os.path.join(LOG_DIR, "auto_loop_log.txt")

DEFAULT_STATE = {
    "project_name": "",
    "project_goal": "",
    "stage": "ready",
    "progress": 0,
    "codex_mode": "실제 Codex CLI",
    "codex_path": "",
    "node_path": "",
    "voice": "준비중",
    "camera": "준비중",
    "last_result": "",
    "last_workspace": WORKSPACE_DIR,
    "last_log_summary": LAST_SUMMARY,
    "auto_loop_enabled": False,
    "auto_loop_max_retry": 2,
    "last_created_files": [],
    "avatar_image": os.path.join(ASSETS_DIR, "mango_avatar.png"),
}
DEFAULT_MEMORY = {"items": []}
DEFAULT_SETTINGS = {
    "chat_font_size": 14,
    "status_font_size": 11,
    "input_font_size": 14,
    "line_spacing": 12,
}
DEFAULT_TASKS = {"queue": []}

def _normalize_path_under_root(path_value: str, fallback: str):
    if not path_value:
        return fallback
    try:
        raw = os.path.abspath(path_value)
        root = os.path.abspath(ROOT_DIR)
        common = os.path.commonpath([raw, root])
        if common == root:
            return raw
    except Exception:
        pass
    return fallback

def _run_hidden(command, **kwargs):
    params = dict(kwargs)
    if os.name == "nt":
        try:
            params["creationflags"] = params.get("creationflags", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        except Exception:
            pass
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            params["startupinfo"] = startupinfo
        except Exception:
            pass
    return subprocess.run(command, **params)

def _load_json(path, default):
    if not os.path.exists(path):
        return default.copy() if isinstance(default, dict) else default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default.copy() if isinstance(default, dict) else default

def _save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def _write_text(path, text):
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write(text or "")

def _append_text(path, text):
    with open(path, "a", encoding="utf-8", errors="replace") as f:
        f.write(text or "")

def add_log(message: str):
    path = os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d')}.log")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    return path

def find_node_path():
    candidates = []
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    candidates.extend([
        os.path.join(program_files, "nodejs", "node.exe"),
        r"C:\Program Files\nodejs\node.exe",
    ])
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        candidates.append(os.path.join(localapp, "Programs", "nodejs", "node.exe"))
    where_path = shutil.which("node")
    if where_path:
        candidates.insert(0, where_path)
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

def find_codex_path():
    candidates = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.extend([
            os.path.join(appdata, "npm", "codex.cmd"),
            os.path.join(appdata, "npm", "codex"),
        ])
    localapp = os.environ.get("LOCALAPPDATA")
    if localapp:
        candidates.extend([
            os.path.join(localapp, "Programs", "nodejs", "codex.cmd"),
            os.path.join(localapp, "Programs", "nodejs", "codex"),
        ])
    where_path = shutil.which("codex.cmd") or shutil.which("codex")
    if where_path:
        candidates.insert(0, where_path)
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

def load_state():
    s = _load_json(STATE_FILE, DEFAULT_STATE)
    for k, v in DEFAULT_STATE.items():
        s.setdefault(k, v)
    if not s.get("codex_path"):
        s["codex_path"] = find_codex_path() or ""
    if not s.get("node_path"):
        s["node_path"] = find_node_path() or ""
    s["last_workspace"] = _normalize_path_under_root(s.get("last_workspace"), WORKSPACE_DIR)
    s["last_log_summary"] = _normalize_path_under_root(s.get("last_log_summary"), LAST_SUMMARY)
    if s["last_workspace"] == WORKSPACE_DIR and s.get("project_name"):
        s["last_workspace"] = ensure_project_workspace(s.get("project_name") or "project")
    return s

def save_state(s):
    _save_json(STATE_FILE, s)

def load_memory():
    m = _load_json(MEMORY_FILE, DEFAULT_MEMORY)
    m.setdefault("items", [])
    return m

def save_memory(m):
    _save_json(MEMORY_FILE, m)

def load_settings():
    s = _load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
    for k, v in DEFAULT_SETTINGS.items():
        s.setdefault(k, v)
    return s

def save_settings(s):
    _save_json(SETTINGS_FILE, s)

def load_tasks():
    t = _load_json(TASKS_FILE, DEFAULT_TASKS)
    t.setdefault("queue", [])
    return t

def save_tasks(t):
    _save_json(TASKS_FILE, t)

def project_slug(name: str):
    safe = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in (name or "project")).strip()
    return "_".join(safe.split())[:40] or "project"

def ensure_project_workspace(name: str):
    slug = project_slug(name)
    path = os.path.join(WORKSPACE_DIR, slug)
    os.makedirs(path, exist_ok=True)
    return path

def ensure_project_assets(workdir: str):
    path = os.path.join(workdir, "assets")
    os.makedirs(path, exist_ok=True)
    return path


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._\-가-힣]+", "_", name).strip("._") or "asset"


def _extract_attachment_paths(text: str):
    lines = (text or "").splitlines()
    paths = []
    in_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[첨부파일]":
            in_block = True
            continue
        if in_block:
            if stripped.startswith("-"):
                p = stripped[1:].strip()
                if p:
                    paths.append(p)
            elif stripped:
                break
    return paths


def _is_image_file(path: str) -> bool:
    return str(path).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))


def prepare_attachment_assets(text: str, workdir: str):
    src_paths = _extract_attachment_paths(text)
    if not src_paths:
        return []
    assets_dir = ensure_project_assets(workdir)
    copied = []
    for raw in src_paths:
        try:
            if not os.path.exists(raw):
                continue
            base = _sanitize_filename(os.path.basename(raw))
            dst = os.path.join(assets_dir, base)
            stem, ext = os.path.splitext(base)
            i = 1
            while os.path.exists(dst):
                try:
                    if os.path.samefile(raw, dst):
                        break
                except Exception:
                    pass
                dst = os.path.join(assets_dir, f"{stem}_{i}{ext}")
                i += 1
            if not os.path.exists(dst):
                shutil.copy2(raw, dst)
            rel = os.path.relpath(dst, workdir).replace("\\", "/")
            copied.append({
                "source": raw,
                "dest": dst,
                "relpath": rel,
                "basename": os.path.basename(dst),
                "is_image": _is_image_file(dst),
            })
        except Exception as e:
            add_log(f"ATTACH COPY FAIL | {raw} | {e}")
    return copied


def _attachment_guidance(copied_assets):
    if not copied_assets:
        return ""
    lines = ["", "첨부 자산:"]
    for asset in copied_assets:
        kind = "image" if asset["is_image"] else "file"
        lines.append(f"- {asset['relpath']} ({kind})")
    image_assets = [a for a in copied_assets if a["is_image"]]
    if image_assets:
        first = image_assets[0]["relpath"]
        lines.extend([
            "",
            "중요 규칙:",
            "- 첨부 이미지를 반드시 실제 UI에 사용해.",
            "- 작업 결과물 코드 안에서 첨부 이미지 경로를 직접 참조해.",
            "- 최소 1개 이상의 UI 요소(헤더/로고/배경/아이콘)에 반드시 반영해.",
            f"- 첫 번째 이미지 우선 사용: {first}",
            "- tkinter GUI면 가능하면 .pyw 파일 기준으로 동작하게 작성해.",
        ])
    return "\n".join(lines)


def _created_files_reference_assets(workdir: str, created_files, copied_assets):
    if not copied_assets:
        return True
    image_assets = [a for a in copied_assets if a["is_image"]]
    if not image_assets:
        return True
    names = [a["basename"] for a in image_assets]
    for name in created_files:
        path = os.path.join(workdir, name)
        if not os.path.isfile(path) or not path.lower().endswith((".py", ".pyw")):
            continue
        try:
            code = open(path, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if any(asset_name in code for asset_name in names):
            return True
    return False


def remember(text: str):
    m = load_memory()
    item = text.replace("망고야", "").replace("기억해", "").replace("메모해", "").strip()
    if not item:
        return "[MANGO] 기억할 내용이 없습니다."
    m["items"].append(item)
    save_memory(m)
    add_log(f"MEMORY ADD | {item}")
    return f"[MANGO] 기억 저장 완료\n\n- {item}"

def get_memory_report():
    items = load_memory().get("items", [])
    if not items:
        return "[MANGO] 저장된 기억이 없습니다."
    return "[MANGO] 저장된 기억\n\n" + "\n".join(f"- {x}" for x in items[-10:])

def start_project(text: str):
    state = load_state()
    raw = text.replace("망고야", "").strip()
    goal = raw
    name = "현재 프로젝트"
    if "|" in raw:
        left, right = [x.strip() for x in raw.split("|", 1)]
        name = left.replace("프로젝트", "").strip() or "현재 프로젝트"
        goal = right
    else:
        cleaned = raw.replace("프로젝트", "").replace("시작해", "").replace("진행해", "").strip()
        if cleaned:
            name = cleaned
    workspace = ensure_project_workspace(name)
    state["project_name"] = name
    state["project_goal"] = goal
    state["stage"] = "project_started"
    state["progress"] = 5
    state["last_workspace"] = workspace
    save_state(state)
    add_log(f"PROJECT | {name} | {goal} | {workspace}")
    return f"[MANGO] 프로젝트 시작\n\n프로젝트: {name}\n목표: {goal}\n작업폴더:\n{workspace}"

def make_outsource_prompt(text: str):
    state = load_state()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DATA_DIR, f"chatgpt_outsource_{ts}.txt")
    content = f"""[ROLE]
너는 ChatGPT 기획/분석 담당이다.

[PROJECT]
{state.get("project_name") or "미지정"}

[GOAL]
{state.get("project_goal") or "미지정"}

[REQUEST]
{text}

[OUTPUT]
- 요구사항 정리
- 추천 구조
- 구현 순서
- 주의점
- Codex에 넘길 작업지시서 초안
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    state["stage"] = "outsource_prompt_generated"
    state["progress"] = max(state.get("progress", 0), 20)
    save_state(state)
    add_log(f"OUTSOURCE PROMPT | {path}")
    return f"[MANGO] ChatGPT 외주 프롬프트 생성 완료\n\n파일:\n{path}"

def make_codex_prompt(text: str):
    state = load_state()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(DATA_DIR, f"codex_task_{ts}.txt")
    workdir = state.get("last_workspace") or ensure_project_workspace(state.get("project_name") or "project")
    copied_assets = prepare_attachment_assets(text, workdir)
    asset_guide = _attachment_guidance(copied_assets)
    content = f"""[ROLE]
너는 Codex CLI 개발 실행 담당이다.

[WORKDIR]
{workdir}

[PROJECT]
{state.get("project_name") or "미지정"}

[GOAL]
{state.get("project_goal") or "미지정"}

[TASK]
{text}{asset_guide}

[OUTPUT]
- 생성/수정 파일 목록
- 실행 명령
- 테스트 결과
- 남은 이슈
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    state["stage"] = "codex_prompt_generated"
    state["progress"] = max(state.get("progress", 0), 35)
    save_state(state)
    add_log(f"CODEX PROMPT | {path}")
    return path

def _fallback_run(text: str, workdir: str):
    generated_path = os.path.join(workdir, "generated_code.py")
    safe_text = text.replace('"', "'")
    code = f'print("AUTO FALLBACK EXECUTED")\nprint("REQUEST: {safe_text}")\n'
    with open(generated_path, "w", encoding="utf-8") as f:
        f.write(code)
    result = _run_hidden(
        [sys.executable, generated_path],
        capture_output=True,
        text=True,
        timeout=20,
        encoding="utf-8",
        errors="replace",
        cwd=workdir,
    )
    return {
        "generated_path": generated_path,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }

def _build_env():
    env = os.environ.copy()
    node_path = find_node_path()
    if node_path:
        env["PATH"] = os.path.dirname(node_path) + os.pathsep + env.get("PATH", "")
    appdata = os.environ.get("APPDATA")
    if appdata:
        env["PATH"] = os.path.join(appdata, "npm") + os.pathsep + env.get("PATH", "")
    return env

def _expected_filename(text: str):
    m = re.search(r'([A-Za-z0-9_\-가-힣]+\.pyw?)', text)
    if m:
        return m.group(1)
    name_match = re.search(r'이름은\s*([A-Za-z0-9_\-가-힣]+)', text)
    explicit_name = name_match.group(1).strip() if name_match else None
    if explicit_name:
        explicit_name = re.sub(r"(으로|로|을|를|이야|야)$", "", explicit_name).strip()
        if not explicit_name.lower().endswith((".py", ".pyw")):
            return explicit_name + ".py"
        return explicit_name
    if "게임" in text:
        return "auto_loop_game.py"
    if "계산기" in text:
        return "calc_app.py"
    if "메모장" in text:
        return "memo_app.py"
    return None

def _run_cmd(command, workdir, env):
    return _run_hidden(
        command,
        capture_output=True,
        text=True,
        timeout=240,
        encoding="utf-8",
        errors="replace",
        cwd=workdir,
        env=env,
        shell=False,
    )

def _verify_environment(codex_path, workdir, env):
    checks = []
    checks.append(_run_cmd(["cmd.exe", "/c", "where", "node"], workdir, env))
    checks.append(_run_cmd(["cmd.exe", "/c", codex_path, "--version"], workdir, env))
    return checks

def _run_codex(codex_path: str, prompt: str, workdir: str):
    env = _build_env()
    checks = _verify_environment(codex_path, workdir, env)

    precheck_stdout = []
    precheck_stderr = []
    for idx, r in enumerate(checks, start=1):
        precheck_stdout.append(f"[precheck {idx} rc={r.returncode}]\n{(r.stdout or '').strip()}")
        precheck_stderr.append(f"[precheck {idx} rc={r.returncode}]\n{(r.stderr or '').strip()}")

    result = _run_hidden(
        ["cmd.exe", "/c", codex_path, "exec", "--skip-git-repo-check", "--full-auto"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8",
        errors="replace",
        cwd=workdir,
        env=env,
        shell=False,
    )

    stdout = "\n\n".join(precheck_stdout + [(result.stdout or "").strip()])
    stderr = "\n\n".join(precheck_stderr + [(result.stderr or "").strip()])
    return result.returncode, stdout, stderr

def _collect_workspace_files(workdir):
    return sorted([f for f in os.listdir(workdir) if os.path.isfile(os.path.join(workdir, f))])

def _is_gui_python_file(path: str) -> bool:
    if not path or not os.path.exists(path) or not path.lower().endswith((".py", ".pyw")):
        return False
    try:
        code = open(path, "r", encoding="utf-8", errors="replace").read().lower()
    except Exception:
        return False
    gui_markers = ["tkinter", "customtkinter", "pyqt", "pyside", "wx.", "dearpygui", "kivy"]
    return any(marker in code for marker in gui_markers)

def _ensure_cmdless_launchers(workdir: str, created_files):
    added = []
    for name in list(created_files):
        path = os.path.join(workdir, name)
        if not _is_gui_python_file(path):
            continue

        base, ext = os.path.splitext(name)
        pyw_name = f"{base}.pyw"
        pyw_path = os.path.join(workdir, pyw_name)
        if ext.lower() == ".py" and not os.path.exists(pyw_path):
            shutil.copyfile(path, pyw_path)
            added.append(pyw_name)

    merged = []
    for name in list(created_files) + added:
        if name.startswith("run_") and name.endswith("_silent.pyw"):
            continue
        if name not in merged:
            merged.append(name)
    return merged

def get_last_launch_error_report():
    if not os.path.exists(LAST_GUI_ERROR):
        return "(없음)"
    try:
        return open(LAST_GUI_ERROR, "r", encoding="utf-8", errors="replace").read().strip()[:400]
    except Exception:
        return LAST_GUI_ERROR

def clear_last_launch_error():
    try:
        if os.path.exists(LAST_GUI_ERROR):
            os.remove(LAST_GUI_ERROR)
    except Exception:
        pass

def get_paths_report():
    state = load_state()
    return {
        "root": ROOT_DIR,
        "workspace_root": WORKSPACE_DIR,
        "project_workspace": state.get("last_workspace") or WORKSPACE_DIR,
        "logs": LOG_DIR,
        "data": DATA_DIR,
        "assets": ASSETS_DIR,
        "avatar_image": state.get("avatar_image") or os.path.join(ASSETS_DIR, "mango_avatar.png"),
        "last_log_summary": state.get("last_log_summary") or LAST_SUMMARY,
    }

def auto_codex_execute(text: str, retry_count=0):
    state = load_state()
    workdir = state.get("last_workspace") or ensure_project_workspace(state.get("project_name") or "project")
    copied_assets = prepare_attachment_assets(text, workdir)
    prompt_path = make_codex_prompt(text)
    codex_path = state.get("codex_path") or find_codex_path()
    node_path = state.get("node_path") or find_node_path()
    expected_file = _expected_filename(text)
    state["codex_path"] = codex_path or ""
    state["node_path"] = node_path or ""
    state["stage"] = "coding"
    state["progress"] = max(state.get("progress", 0), 55)
    save_state(state)

    if not codex_path:
        fb = _fallback_run(text, workdir)
        state = load_state()
        state["stage"] = "failed"
        state["progress"] = 70
        state["last_result"] = fb["stdout"] or fb["stderr"]
        state["last_created_files"] = _ensure_cmdless_launchers(workdir, _collect_workspace_files(workdir))
        save_state(state)
        _write_text(LAST_STDOUT, fb["stdout"])
        _write_text(LAST_STDERR, fb["stderr"])
        _write_text(LAST_SUMMARY, f"Codex 경로를 찾지 못해 fallback 실행\n파일: {fb['generated_path']}")
        return f"[MANGO] Codex 경로 없음\n\n로그 요약:\n{LAST_SUMMARY}"

    try:
        instruction = (
            f"작업 폴더: {workdir}\n"
            f"요청: {text}\n"
            "분석만 하지 말고 반드시 실제 파일을 생성 또는 수정해.\n"
            "대답만 하지 말고 결과 파일을 작업 폴더에 남겨.\n"
            "작업 완료 후 마지막에 생성/수정한 파일명을 한 줄로 적어."
        )
        rc, stdout, stderr = _run_codex(codex_path, instruction, workdir)

        _write_text(LAST_STDOUT, stdout)
        _write_text(LAST_STDERR, stderr)

        created_files = _collect_workspace_files(workdir)
        created_files = _ensure_cmdless_launchers(workdir, created_files)
        expected_exists = expected_file and os.path.exists(os.path.join(workdir, expected_file))
        assets_referenced = _created_files_reference_assets(workdir, created_files, copied_assets)

        if rc != 0 or (expected_file and not expected_exists) or not assets_referenced:
            summary = (
                "Codex CLI 실행 실패 또는 기대 파일 미생성\n"
                f"codex rc: {rc}\n"
                f"codex path: {codex_path}\n"
                f"node path: {node_path or '(없음)'}\n"
                f"workspace: {workdir}\n"
                f"expected file: {expected_file or '(미지정)'}\n"
                f"expected exists: {expected_exists}\n"
                f"workspace files: {', '.join(created_files) or '(없음)'}\n"
                f"stdout log: {LAST_STDOUT}\n"
                f"stderr log: {LAST_STDERR}\n"
                f"retry count: {retry_count}\n"
            )
            _write_text(LAST_SUMMARY, summary)
            state = load_state()
            state["stage"] = "failed"
            state["progress"] = 70
            state["last_result"] = stderr or stdout
            state["last_log_summary"] = LAST_SUMMARY
            state["last_created_files"] = created_files
            save_state(state)
            add_log(f"CODEX EXEC FAIL | path={codex_path} | node={node_path} | rc={rc} | expected={expected_file} | exists={expected_exists} | retry={retry_count}")

            if state.get("auto_loop_enabled") and retry_count < int(state.get("auto_loop_max_retry", 2)):
                _append_text(AUTO_LOOP_LOG, f"[retry {retry_count+1}] expected file missing or rc error\n")
                repair_text = (
                    f"{text}\n"
                    f"이전 시도 실패. 반드시 {expected_file or '결과 파일'} 를 작업 폴더에 실제 생성해.\n"
                    "설명만 하지 말고 파일부터 만들어."
                )
                return auto_codex_execute(repair_text, retry_count=retry_count+1)

            fb = _fallback_run(text, workdir)
            _append_text(AUTO_LOOP_LOG, f"[fallback] {fb['generated_path']}\n")
            return f"[MANGO] Codex 실행 실패\n\n로그 요약:\n{LAST_SUMMARY}"

        summary = (
            "Codex CLI 자동 실행 완료\n"
            f"codex rc: {rc}\n"
            f"codex path: {codex_path}\n"
            f"node path: {node_path or '(없음)'}\n"
            f"workspace: {workdir}\n"
            f"expected file: {expected_file or '(미지정)'}\n"
            f"workspace files: {', '.join(created_files) or '(없음)'}\n"
            f"stdout log: {LAST_STDOUT}\n"
            f"stderr log: {LAST_STDERR}\n"
            f"retry count: {retry_count}\n"
        )
        _write_text(LAST_SUMMARY, summary)
        state = load_state()
        state["stage"] = "done"
        state["progress"] = 100
        state["last_result"] = stdout or stderr
        state["last_log_summary"] = LAST_SUMMARY
        state["last_created_files"] = created_files
        save_state(state)
        add_log(f"CODEX EXEC OK | path={codex_path} | node={node_path} | rc={rc} | files={created_files}")
        _append_text(AUTO_LOOP_LOG, f"[success] retry={retry_count} files={created_files}\n")
        gui_launchers = [x for x in created_files if x.endswith(".pyw")]
        launcher_text = "\n".join(f"- {x}" for x in gui_launchers[:10]) if gui_launchers else "(없음)"
        return f"[MANGO] Codex 실행 완료\n\n로그 요약:\n{LAST_SUMMARY}\n\nGUI 앱은 .pyw 파일 실행 권장:\n{launcher_text}"
    except Exception as e:
        _write_text(LAST_RUNTIME, str(e))
        fb = _fallback_run(text, workdir)
        summary = (
            "Codex CLI 예외 발생\n"
            f"exception log: {LAST_RUNTIME}\n"
            f"fallback file: {fb['generated_path']}\n"
            f"workspace: {workdir}\n"
            f"retry count: {retry_count}\n"
        )
        _write_text(LAST_SUMMARY, summary)
        state = load_state()
        state["stage"] = "failed"
        state["progress"] = 70
        state["last_result"] = str(e)
        state["last_log_summary"] = LAST_SUMMARY
        state["last_created_files"] = _ensure_cmdless_launchers(workdir, _collect_workspace_files(workdir))
        save_state(state)
        add_log(f"CODEX EXEC ERROR | path={codex_path} | node={node_path} | {e}")
        _append_text(AUTO_LOOP_LOG, f"[exception] retry={retry_count} {e}\n")
        return f"[MANGO] Codex 예외 발생\n\n로그 요약:\n{LAST_SUMMARY}"

def enable_auto_loop():
    state = load_state()
    state["auto_loop_enabled"] = True
    save_state(state)
    _append_text(AUTO_LOOP_LOG, "[mode] enabled\n")
    return "[MANGO] 자동 루프 개발 모드 ON"

def disable_auto_loop():
    state = load_state()
    state["auto_loop_enabled"] = False
    save_state(state)
    _append_text(AUTO_LOOP_LOG, "[mode] disabled\n")
    return "[MANGO] 자동 루프 개발 모드 OFF"

def auto_loop_status():
    state = load_state()
    return (
        "[MANGO] 자동 루프 상태\n\n"
        f"- enabled: {state.get('auto_loop_enabled')}\n"
        f"- max_retry: {state.get('auto_loop_max_retry')}\n"
        f"- log: {AUTO_LOOP_LOG}"
    )

def enqueue_task(task_type: str, payload: str):
    tasks = load_tasks()
    task = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S_%f"),
        "type": task_type,
        "payload": payload,
        "status": "queued",
    }
    tasks["queue"].append(task)
    save_tasks(tasks)
    add_log(f"TASK ENQUEUE | {task_type} | {payload}")
    return task

def run_task_queue():
    tasks = load_tasks()
    if not tasks["queue"]:
        return "[MANGO] 작업 큐가 비어 있습니다."
    results = []
    for task in tasks["queue"]:
        if task.get("status") != "queued":
            continue
        task["status"] = "running"
        save_tasks(tasks)
        if task["type"] == "outsource":
            res = make_outsource_prompt(task["payload"])
        elif task["type"] == "codex":
            res = auto_codex_execute(task["payload"])
        else:
            res = "[MANGO] 지원하지 않는 작업 타입"
        task["status"] = "done"
        task["result"] = res
        save_tasks(tasks)
        results.append(f"- {task['type']} 완료")
    state = load_state()
    state["stage"] = "queue_done"
    state["progress"] = max(state.get("progress", 0), 90)
    save_state(state)
    return "[MANGO] 작업 큐 실행 완료\n\n" + "\n".join(results)

def start_auto_loop(goal_text: str):
    state = load_state()
    state["auto_loop_enabled"] = True
    save_state(state)
    _write_text(AUTO_LOOP_LOG, f"[start] {datetime.now().isoformat()}\n")
    enqueue_task("outsource", goal_text)
    enqueue_task("codex", goal_text)
    return run_task_queue()

def make_demo():
    demo_path = os.path.join(TEMP_DIR, "demo_generated.py")
    with open(demo_path, "w", encoding="utf-8") as f:
        f.write("print('MANGO demo run OK')\n")
    log_path = add_log(f"DEMO GENERATED | {demo_path}")
    return f"[MANGO] 데모 파일 생성 완료\n\n파일:\n{demo_path}\n로그:\n{log_path}"

def cleanup_temp():
    removed = []
    for name in os.listdir(TEMP_DIR):
        path = os.path.join(TEMP_DIR, name)
        try:
            if os.path.isfile(path):
                os.remove(path)
                removed.append(name)
        except Exception:
            pass
    return "[MANGO] temp 정리 완료\n\n" + ("\n".join(f"- {x}" for x in removed) if removed else "(삭제 파일 없음)")

def report():
    state = load_state()
    memory = load_memory()
    tasks = load_tasks()
    queued = len([x for x in tasks["queue"] if x.get("status") == "queued"])
    return (
        "[MANGO] 현재 보고\n\n"
        f"- 루트폴더: {ROOT_DIR}\n"
        f"- workspace: {WORKSPACE_DIR}\n"
        f"- archive: {ARCHIVE_DIR}\n"
        f"- assets: {ASSETS_DIR}\n"
        f"- 프로젝트: {state.get('project_name') or '없음'}\n"
        f"- 목표: {state.get('project_goal') or '없음'}\n"
        f"- 단계: {state.get('stage')}\n"
        f"- 진행률: {state.get('progress', 0)}%\n"
        f"- Codex 경로: {state.get('codex_path') or '(없음)'}\n"
        f"- Node 경로: {state.get('node_path') or '(없음)'}\n"
        f"- 자동 루프: {state.get('auto_loop_enabled')}\n"
        f"- 최근 파일: {', '.join(state.get('last_created_files', [])) or '(없음)'}\n"
        f"- 로그 요약: {state.get('last_log_summary') or LAST_SUMMARY}\n"
        f"- 기억 개수: {len(memory.get('items', []))}\n"
        f"- 대기 작업: {queued}"
    )

def chat(text: str):
    t = (text or "").strip()
    if t in ["안녕", "안녕하세요", "망고야", "hello"]:
        return "[MANGO] 안녕하세요.\n\n지금은 총괄 집사형 오케스트레이터로 대기 중입니다."
    return "[MANGO] 일반 대화는 아직 약합니다.\n\n프로젝트 시작, 외주, 코드, 보고, 기억, 자동 루프 요청을 하면 더 잘 움직입니다."
