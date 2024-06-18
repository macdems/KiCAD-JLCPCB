import unicodedata as ud

def rmdiacritics(char):
    """
    Return the base character of char, by "removing" any
    diacritics like accents or curls and strokes and the like.
    """
    desc = ud.name(char)
    cutoff = desc.find(' WITH ')
    if cutoff != -1:
        desc = desc[:cutoff]
        try:
            char = ud.lookup(desc)
        except KeyError:
            pass  # removing "WITH ..." produced an invalid name
    return char


def normalize(string):
    """
    Return a string with the same meaning as string, but with
    "simpler" characters, e.g., "é" => "e", "ç" => "c", etc.
    """
    return "".join(rmdiacritics(c) for c in string)
