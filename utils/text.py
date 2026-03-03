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
