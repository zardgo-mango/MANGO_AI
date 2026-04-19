from pathlib import Path


class MangoEngine:
    def __init__(self, workspace_dir="workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate_input(self, command, attachments):
        command = (command or "").strip()

        if not command:
            return False, "명령이 비어 있습니다."

        if not attachments:
            return False, "첨부 파일이 없습니다."

        valid_files = []
        for item in attachments:
            p = Path(item)
            if p.exists() and p.is_file():
                try:
                    if p.stat().st_size > 0:
                        valid_files.append(str(p))
                except OSError:
                    pass

        if not valid_files:
            return False, "유효한 첨부 파일이 없습니다."

        return True, "OK"

    def needs_spec(self, command):
        text = (command or "").strip()
        keywords = [
            "만들어줘",
            "제작",
            "개발",
            "프로그램",
            "앱",
            "게임",
            "사이트",
            "자동화",
            "시스템",
        ]
        return any(k in text for k in keywords)

    def build_spec_file(self, command):
        path = self.workspace_dir / "task_spec.txt"

        lines = [
            "[MANGO 맞춤 시방서]",
            "",
            f"원본 요청: {command}",
            "",
            "아래 항목을 작성하세요.",
            "",
            "1. 작업 목표",
            "2. 대상 플랫폼",
            "3. 필수 기능",
            "4. 선택 기능",
            "5. 입력 자료",
            "6. 출력 결과물",
            "7. 디자인 요구사항",
            "8. 제약 사항",
            "9. 완료 기준",
            "",
            "첨부 자료가 있으면 함께 넣어주세요.",
        ]

        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def execute_once(self, command, attachments):
        ok, msg = self.validate_input(command, attachments)
        if not ok:
            raise ValueError(msg)

        if self.needs_spec(command):
            spec_path = self.build_spec_file(command)
            return {
                "status": "NEEDS_SPEC",
                "message": "추상 명령 감지: 시방서 작성 필요",
                "spec_path": spec_path,
            }

        return {
            "status": "DONE",
            "message": "작업 1회 실행 완료",
            "spec_path": None,
        }
