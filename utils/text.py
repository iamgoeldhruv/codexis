import tiktoken
def get_tokenizer(model:str):
    try:
        encoding=tiktoken.encoding_for_model(model)
        return encoding.encode
    except Exception:
        encoding=tiktoken.get_encoding("cl100k_base")
        return encoding.encode

def count_tokens(text:str,model:str)->int:
    tokenizer=get_tokenizer(model)
    if tokenizer:
        return len(tokenizer(text))

    else:
        return estimate_token(text)

def estimate_token(text:str)->int:
    number_of_tokens=len(text)//4
    return max(1,number_of_tokens)