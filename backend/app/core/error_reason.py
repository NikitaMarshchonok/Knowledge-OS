import re


def normalize_reason_token(reason: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", reason.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "unknown"


def classify_failure_reason(detail: str) -> str:
    text = detail.lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if (
        "unreachable" in text
        or "connection refused" in text
        or "connection reset" in text
        or "name or service not known" in text
        or "temporary failure" in text
        or "http error" in text
    ):
        return "provider_error"
    if "invalid response payload" in text or "empty answer" in text:
        return "llm_error"
    return "exception"


def format_error_message(category: str, reason: str, detail: str | None = None) -> str:
    category_token = normalize_reason_token(category)
    reason_token = normalize_reason_token(reason)
    base = f"{category_token}:{reason_token}"
    if not detail:
        return base
    compact_detail = " ".join(detail.split())[:220]
    return f"{base} ({compact_detail})"


def extract_error_reason(error_message: str | None) -> str | None:
    if not error_message:
        return None
    cleaned = error_message.strip()
    if not cleaned:
        return None
    if ":" not in cleaned:
        return classify_failure_reason(cleaned)

    _, remainder = cleaned.split(":", 1)
    remainder = remainder.strip()
    if not remainder:
        return "unknown"

    match = re.match(r"([a-z0-9_]+)", remainder.lower())
    if match:
        return normalize_reason_token(match.group(1))
    return "unknown"


def extract_error_category(error_message: str | None) -> str | None:
    if not error_message:
        return None
    cleaned = error_message.strip()
    if not cleaned:
        return None
    if ":" not in cleaned:
        return "failed"
    category, _ = cleaned.split(":", 1)
    normalized = normalize_reason_token(category)
    return normalized or None
