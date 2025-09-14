import re


def detect_srs_ids(text: str, pattern: str):
    try:
        return list(dict.fromkeys(re.findall(pattern, text) and re.findall(pattern, text, flags=re.IGNORECASE) or re.findall(pattern, text)))
    except re.error:
        # fallback om regex ej kompilerar
        return []


def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")
