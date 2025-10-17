from typing import List

PHILLY_SLANG = {
    "you": "youse",
    "person": "bol",
    "people": "bols",
    "guy": "jawn",
    "guys": "jawns",
    "girl": "jawn",
    "girls": "jawns",
    "sandwich": "hoagie",
    "sandwiches": "hoagies",
    "friend": "jawn",
    "friends": "jawns",
    "thing": "jawn",
    "things": "jawns",
    "car": "whip",
    "cars": "whips",
    "house": "jawn",
    "houses": "jawns",
    "dog": "pup",
    "dogs": "pups",
}


def convert_to_philly_slang(nlp, text: str) -> str:
    doc = nlp(text)
    out: List[str] = []
    for token in doc:
        base = token.text.lower()
        if token.pos_ == "NOUN" and base in PHILLY_SLANG:
            out.append(PHILLY_SLANG[base])
        elif token.pos_ == "NOUN":
            out.append("jawn" if token.tag_ != "NNS" else "jawns")
        else:
            out.append(token.text)

    s = ""
    for tok, orig in zip(out, doc):
        if orig.is_punct:
            s += tok
        else:
            s += (" " + tok)
    return s.strip()


__all__ = ["convert_to_philly_slang"]
