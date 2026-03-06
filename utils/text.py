import tiktoken


def get_tokenizer(model: str):
    try:
        encoding = tiktoken.encoding_for_model(model)
        return encoding.encode
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode


def count_tokens(text: str, model: str) -> int:
    tokenizer = get_tokenizer(model)
    if tokenizer:
        return len(tokenizer(text))

    else:
        return estimate_token(text)


def estimate_token(text: str) -> int:
    number_of_tokens = len(text) // 4
    return max(1, number_of_tokens)


def _truncate_by_chars(text: str, target_tokens: int, model: str, suffix: str) -> str:
    low, high = 0, len(text)

    while low < high:
        mid = (low + high + 1) // 2
        if count_tokens(text[:mid], model) <= target_tokens:
            low = mid
        else:
            high = mid - 1

    return text[:low] + suffix


def _truncate_by_lines(text: str, target_tokens: int, model: str, suffix: str) -> str:
    lines = text.split("\n")
    result_lines: list[str] = []
    current_tokens = 0
    for line in lines:
        line_tokens = count_tokens(line, model)
        if current_tokens + line_tokens >= target_tokens:
            break
        result_lines.append(line)
        current_tokens += line_tokens
    if not result_lines:
        return _truncate_by_chars(text, target_tokens, model, suffix)
    return "\n".join(result_lines) + suffix


def truncate_text(
    text: str,
    max_token: int,
    model: str,
    preserve_lines: bool = True,
    suffix: str = "\n...[truncated]",
) -> str:
    current_tokens = count_tokens(text, model)
    if current_tokens <= max_token:
        return text
    else:
        suffix_tokens = count_tokens(suffix, model)
        target_tokens = max_token = suffix_tokens
        if target_tokens <= 0:
            return suffix.strip()
        if preserve_lines:
            return _truncate_by_lines(text, target_tokens, model, suffix)
        else:
            return _truncate_by_chars(text, target_tokens, model, suffix)
        
