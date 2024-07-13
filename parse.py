def signed_char(n: int, a: str, b: str) -> str:
    if n>=0: return a*n
    else:    return b*(-n)

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except:
        return False
