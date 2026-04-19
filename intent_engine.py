def detect_intent(text: str) -> str:
    t = (text or "").strip().lower()
    if any(k in t for k in ["프로젝트", "시작", "진행"]):
        return "project"
    if any(k in t for k in ["외주", "정리", "리스트", "아키텍처", "기획"]):
        return "outsource"
    if any(k in t for k in ["자동 루프", "자동개발", "자동 개발", "반복 개발", "자가수정", "자가 수정"]):
        return "auto_loop"
    if any(k in t for k in ["코드", "구현", "만들어", "개발", "테스트", "수정", "프로그램"]):
        return "codex"
    if any(k in t for k in ["상태", "보고", "현황"]):
        return "report"
    if any(k in t for k in ["기억", "메모", "remember", "memory"]):
        return "memory"
    if any(k in t for k in ["자동", "루프", "계속", "반복"]):
        return "auto_loop"
    return "chat"
