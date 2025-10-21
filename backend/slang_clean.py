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
    # Iterate by index so we can detect the next token reliably (doc.index
    # is unsafe when duplicate token text exists).
    for i, token in enumerate(doc):
        base = token.text.lower()
        # Map ChatGPT to a playful localized name
        if base == "chatgpt":
            out.append("Philly friggin' GPT")
            continue
        # If this token is a noun and the next token is also a noun, leave
        # this token unchanged; only translate the final noun in a run of
        # adjacent nouns.
        next_is_noun = False
        if (i + 1) < len(doc):
            next_tok = doc[i + 1]
            next_is_noun = next_tok.pos_ == "NOUN"

        if token.pos_ == "NOUN" and next_is_noun:
            out.append(token.text)
        elif token.pos_ == "NOUN" and base in PHILLY_SLANG:
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
