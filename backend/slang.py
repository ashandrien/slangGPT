from typing import List, Union
import json
import random
import os
from pathlib import Path

# Generic, configurable slang mapping loader.
# Default file is `backend/data/slang.json`; fall back to the historic
# `philly_slang.json` if present for backwards compatibility.
_module_dir = Path(__file__).resolve().parent
_default_file = _module_dir / "data" / "slang.json"
_fallback_file = _module_dir / "data" / "philly_slang.json"

# Allow override via environment variable SLANG_FILE (absolute or relative
# to the backend module directory).
_env_path = os.getenv("SLANG_FILE")
if _env_path:
    _data_path = Path(_env_path) if Path(_env_path).is_absolute() else _module_dir / _env_path
else:
    _data_path = _default_file if _default_file.exists() else _fallback_file

# Track mtime so we can reload dynamic edits without restarting the server.
_slang_mtime = None
if _data_path and _data_path.exists():
    try:
        SLANG_MAP = json.loads(_data_path.read_text(encoding="utf8"))
        try:
            _slang_mtime = _data_path.stat().st_mtime
        except Exception:
            _slang_mtime = None
    except Exception:
        SLANG_MAP = {}
else:
    # Reasonable minimal fallback mapping so the app is still usable for demo.
    SLANG_MAP = {
        "person": ["friend"],
        "people": ["friends"],
        "sandwich": ["sandwich"],
        "car": ["car"],
    }


def reload_slang_mapping() -> None:
    """Reload the SLANG_MAP mapping from the JSON file on disk.

    This updates the module-level SLANG_MAP mapping and the cached
    modification time so future calls can detect changes.
    """
    global SLANG_MAP, _slang_mtime, _data_path
    try:
        if _data_path and _data_path.exists():
            SLANG_MAP = json.loads(_data_path.read_text(encoding="utf8"))
            try:
                _slang_mtime = _data_path.stat().st_mtime
            except Exception:
                _slang_mtime = None
    except Exception:
        # If reload fails, keep the previous mapping and mtime
        return

# Backwards-compatible name for reload helper
reload_philly_slang = reload_slang_mapping


def pluralize_slang(slang: str) -> str:
    """Very small pluralize helper used if needed."""
    if slang.endswith("y"):
        return slang[:-1] + "ies"
    return slang + "s"


def convert_to_philly_slang(nlp, text: str) -> str:
    """Convert input text to a configured local slang using the provided spaCy `nlp`.

    Note: the function name is kept for compatibility with existing callers
    (for example `backend.main`) but the mapping it uses is generic and
    loaded from `SLANG_MAP` (loaded from `data/slang.json` by default).
    """
    # Auto-reload mapping if the JSON file changed on disk since we last
    # loaded it. This allows editing the JSON file to take effect without
    # restarting the backend.
    try:
        if _data_path and _data_path.exists():
            mtime = _data_path.stat().st_mtime
            if _slang_mtime is None or mtime != _slang_mtime:
                reload_slang_mapping()
    except Exception:
        # Non-fatal: proceed with the currently loaded mapping
        pass

    doc = nlp(text)

    output = ""
    # Process sentence-by-sentence so we can limit noun replacements per sentence
    inserted_adj_noun = False
    inserted_adverb = False

    for sent in doc.sents:
        noun_replacements = 0
        first_noun_skipped = False
        i = 0
        while i < len(sent):
            token = sent[i]
            replacement = token.text
            whitespace = token.whitespace_

            if not inserted_adverb and token.pos_ == "ADV":
                inserted = "Friggin'" if token.text and token.text[0].isupper() else "friggin'"
                output += inserted + " "
                inserted_adverb = True

            if token.text.lower() == "you" and (i + 1) < len(sent):
                next_tok = sent[i + 1]
                if next_tok.text.lower() == "all":
                    phrase_key = "you all"
                    candidate = SLANG_MAP.get(phrase_key)
                    if candidate:
                        pick = random.choice(candidate) if isinstance(candidate, list) else candidate
                        if token.text and token.text[0].isupper():
                            pick = pick.capitalize()
                        replacement = pick
                        whitespace = next_tok.whitespace_
                        i += 2
                        output += replacement + whitespace
                        continue

            base = token.text.lower()
            if base == "chatgpt":
                replacement = "Local friggin' GPT"
                output += replacement + whitespace
                i += 1
                continue
            is_plural = token.tag_ == "NNS"

            if (
                not inserted_adj_noun
                and token.pos_ == "ADJ"
                and (i + 1) < len(sent)
                and sent[i + 1].pos_ in ("NOUN", "PROPN")
            ):
                inserted = "Friggin'" if token.is_sent_start and token.text and token.text[0].isupper() else "friggin'"
                output += token.text + whitespace + inserted + " "
                inserted_adj_noun = True
                i += 1
                continue

            if token.pos_ == "PRON":
                if base in SLANG_MAP:
                    candidate = SLANG_MAP.get(base)
                    pick = random.choice(candidate) if isinstance(candidate, list) else candidate
                    if token.text and token.text[0].isupper():
                        pick = pick.capitalize()
                    replacement = pick
                else:
                    replacement = token.text
                output += replacement + whitespace
                i += 1
                continue

            if token.pos_ in ("NOUN", "PROPN"):
                if (i + 1) < len(sent) and sent[i + 1].pos_ in ("NOUN", "PROPN"):
                    if not first_noun_skipped:
                        first_noun_skipped = True
                    output += token.text + whitespace
                    i += 1
                    continue
                if not first_noun_skipped:
                    first_noun_skipped = True
                    output += token.text + whitespace
                    i += 1
                    continue

                if base in SLANG_MAP:
                    if noun_replacements < 3:
                        candidate: Union[str, List[str]] = SLANG_MAP.get(base)
                        pick = random.choice(candidate) if isinstance(candidate, list) else candidate
                        if token.pos_ == "NOUN" and is_plural:
                            pick = pluralize_slang(pick)
                        if token.text and token.text[0].isupper():
                            pick = pick.capitalize()
                        replacement = pick
                        noun_replacements += 1
                    else:
                        replacement = token.text
                    output += replacement + whitespace
                    i += 1
                    continue
                else:
                    if noun_replacements < 3:
                        replacement = "jawn" if not is_plural else "jawns"
                        noun_replacements += 1
                    else:
                        replacement = token.text
                    output += replacement + whitespace
                    i += 1
                    continue

            output += replacement + whitespace
            i += 1

    return output.strip()


__all__ = [
    "convert_to_philly_slang",
    "reload_slang_mapping",
    "SLANG_MAP",
    "set_slang_file",
    "pluralize_slang",
]


def set_slang_file(pathlike: str) -> bool:
    """Set the module's slang JSON file and reload the mapping.

    Accepts either an absolute path or a path relative to the backend module
    directory. Returns True on success, False on failure. This is intentionally
    permissive for local/dev use; callers should validate filenames when used
    from untrusted sources.
    """
    global _data_path, _slang_mtime
    try:
        cand = Path(pathlike)
        if not cand.is_absolute():
            cand = _module_dir / pathlike
        # Basic safety: require the file to exist and be under the backend/data dir
        data_dir = _module_dir / "data"
        try:
            cand_resolved = cand.resolve()
            # ensure it's underneath backend/data
            if data_dir.resolve() not in cand_resolved.parents and cand_resolved != data_dir.resolve():
                return False
        except Exception:
            return False
        if not cand.exists() or not cand.is_file():
            return False
        _data_path = cand
        reload_slang_mapping()
        return True
    except Exception:
        return False