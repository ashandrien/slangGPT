from typing import List, Union
import json
import random
from pathlib import Path

# Load the PHILLY_SLANG mapping from data/philly_slang.json if present. This
# keeps the data separate from code so editors and translators can update it
# without touching Python.
_data_path = Path(__file__).resolve().parent / "data" / "philly_slang.json"
# Track the file mtime so we can reload the mapping at runtime when the file
# changes on disk. Initialize PHILLY_SLANG and _philly_slang_mtime from disk
# if possible.
_philly_slang_mtime = None
if _data_path.exists():
    try:
        PHILLY_SLANG = json.loads(_data_path.read_text(encoding="utf8"))
        try:
            _philly_slang_mtime = _data_path.stat().st_mtime
        except Exception:
            _philly_slang_mtime = None
    except Exception:
        PHILLY_SLANG = {}
else:
    # Fallback mapping if the JSON file is missing or unreadable
    # Use list-valued fallbacks for consistency with the JSON file format
    PHILLY_SLANG = {
        "person": ["bol"],
        "people": ["bols"],
        "girl": ["jawn"],
        "girls": ["jawns"],
        "sandwich": ["hoagie"],
        "sandwiches": ["hoagies"],
        "friend": ["jawn"],
        "friends": ["jawns"],
        "thing": ["jawn"],
        "things": ["jawns"],
        "car": ["whip"],
        "cars": ["whips"],
        "house": ["crib"],
        "houses": ["cribs"],
        "dog": ["pup"],
        "dogs": ["pups"],
    }


def reload_philly_slang() -> None:
    """Reload the PHILLY_SLANG mapping from the JSON file on disk.

    This updates the module-level PHILLY_SLANG mapping and the cached
    modification time so future calls can detect changes.
    """
    global PHILLY_SLANG, _philly_slang_mtime
    try:
        if _data_path.exists():
            PHILLY_SLANG = json.loads(_data_path.read_text(encoding="utf8"))
            try:
                _philly_slang_mtime = _data_path.stat().st_mtime
            except Exception:
                _philly_slang_mtime = None
    except Exception:
        # If reload fails, keep the previous mapping and mtime
        return


def pluralize_slang(slang: str) -> str:
    """Very small pluralize helper used if needed."""
    if slang.endswith("y"):
        return slang[:-1] + "ies"
    return slang + "s"


def convert_to_philly_slang(nlp, text: str) -> str:
    """Convert input text to Philly slang using the provided spaCy `nlp`.

    Args:
        nlp: a spaCy Language instance (e.g. spacy.load(...))
        text: input text to convert

    Returns:
        Converted text as a string.
    """
    # Auto-reload mapping if the JSON file changed on disk since we last
    # loaded it. This allows editing `backend/data/philly_slang.json` to take
    # effect without restarting the backend.
    try:
        if _data_path.exists():
            mtime = _data_path.stat().st_mtime
            if _philly_slang_mtime is None or mtime != _philly_slang_mtime:
                reload_philly_slang()
    except Exception:
        # Non-fatal: proceed with the currently loaded mapping
        pass

    doc = nlp(text)
    out_tokens: List[str] = []
    skip_next = False
    for i, token in enumerate(doc):
        if skip_next:
            skip_next = False
            continue

        # Handle multi-token phrase 'you all' (case-insensitive)
        if token.text.lower() == "you" and (i + 1) < len(doc):
            next_tok = doc[i + 1]
            if next_tok.text.lower() == "all":
                # Found 'you all' -> check mapping for the phrase
                phrase_key = "you all"
                candidate = PHILLY_SLANG.get(phrase_key)
                if candidate:
                    pick = random.choice(candidate) if isinstance(candidate, list) else candidate
                    # Preserve capitalization if the first token was capitalized
                    if token.text[0].isupper():
                        pick = pick.capitalize()
                    out_tokens.append(pick)
                    skip_next = True
                    continue

        is_plural = token.tag_ == "NNS"
        base = token.text.lower()

        # Explicitly exempt personal pronouns from default conversion.
        # Only convert pronouns if they are explicitly present in PHILLY_SLANG
        if token.pos_ == "PRON":
            if base in PHILLY_SLANG:
                candidate = PHILLY_SLANG.get(base)
                pick = random.choice(candidate) if isinstance(candidate, list) else candidate
                if token.text and token.text[0].isupper():
                    pick = pick.capitalize()
                out_tokens.append(pick)
            else:
                out_tokens.append(token.text)
            continue

        # Handle nouns and proper nouns. If a mapping exists, use it; if not,
        # fallback to 'jawn'/'jawns' for nouns only.
        if token.pos_ in ("NOUN", "PROPN") and base in PHILLY_SLANG:
            candidate: Union[str, List[str]] = PHILLY_SLANG.get(base)
            if isinstance(candidate, list):
                pick = random.choice(candidate)
            else:
                pick = candidate

            # Apply pluralization for nouns
            if token.pos_ == "NOUN" and is_plural:
                pick = pluralize_slang(pick)

            if token.text and token.text[0].isupper():
                pick = pick.capitalize()

            out_tokens.append(pick)
        elif token.pos_ == "NOUN":
            out_tokens.append("jawn" if not is_plural else "jawns")
        else:
            out_tokens.append(token.text)

    # Reconstruct text preserving punctuation spacing
    # Reconstruct text preserving punctuation spacing. Note that out_tokens
    # may be shorter than doc when multi-token phrases were replaced by a
    # single output token; we iterate through out_tokens and use spacing rules
    # based on the next original token in the doc where possible.
    output = ""
    doc_iter = iter(doc)
    for out_tok in out_tokens:
        # Advance doc_iter until we reach a non-space token to check punctuation
        orig = next(doc_iter, None)
        # If orig is punctuation, append directly, otherwise prepend a space
        if orig is not None and orig.is_punct:
            output += out_tok
        else:
            output += (" " + out_tok)
    return output.strip()


__all__ = ["convert_to_philly_slang", "PHILLY_SLANG", "pluralize_slang"]