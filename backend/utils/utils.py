def to_int(s):
    try:
        return int(s)
    except ValueError:
        return None
    except Exception:
        return None
