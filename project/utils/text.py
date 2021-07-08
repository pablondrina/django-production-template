import binascii


def str2hex(text):
    """Convert a string to Hex"""
    encoded = binascii.hexlify(bytes(text, "utf-8"))
    encoded = str(encoded).strip("b")
    encoded = encoded.strip("'")
    return encoded

def to_utf8(text):
    """Convert a string to UTF-8"""
    encoded = text.encode('utf8')
    encoded = str(encoded).strip("b")
    # encoded = encoded.strip("'")
    return encoded