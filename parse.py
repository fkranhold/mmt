def signed_char(n: int, a: str, b: str) -> str:
    if n>=0: return a*n
    else:    return b*(-n)

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except:
        return False

def updown(i: int) -> str:
    return "up" if i > 0 else "down"

def plural(i: int) -> str:
    return "s" if i > 1 else ""

def supdex(i: int) -> str:
    if i > 1: return str(i).translate(str.maketrans("0123456789","⁰¹²³⁴⁵⁶⁷⁸⁹"))
    else:     return ""
