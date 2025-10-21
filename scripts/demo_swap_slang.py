#!/usr/bin/env python3
"""Demo swapping the slang mapping locally.

This script sets SLANG_FILE to the given mapping, imports the backend slang
conversion, and prints a converted example. It does not require the web server
to be running, but it does require a callable `nlp` object; for demo purposes we
use a tiny spaCy-free stub that tokenizes on whitespace and fakes minimal
attributes used by the conversion routine.
"""
import os
import importlib
import sys
from pathlib import Path


class _Token:
    def __init__(self, text):
        self.text = text
        self.whitespace_ = " "
        self.pos_ = "NOUN" if text.isalpha() else "X"
        self.tag_ = "NNS" if text.endswith("s") else "NN"
        self.is_sent_start = True


class _Doc(list):
    def __init__(self, text):
        toks = [t for t in text.split()]
        super().__init__([_Token(t) for t in toks])
        # naive single sentence
        self.sents = [self]


class _NLPSimple:
    def __call__(self, text):
        return _Doc(text)


def demo(mapping_path: Path, text: str):
    os.environ["SLANG_FILE"] = str(mapping_path)
    # reload the slang module so it picks up the env change
    # Ensure repo root is on sys.path so `import backend` works when running the script
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    import backend.slang as slang_mod
    importlib.reload(slang_mod)

    # Use a minimal nlp stub
    nlp = _NLPSimple()
    converted = slang_mod.convert_to_philly_slang(nlp, text)
    print(f"Mapping file: {mapping_path}")
    print(f"Original: {text}")
    print(f"Converted: {converted}")


def main(argv):
    root = Path(__file__).resolve().parent.parent
    default = root / "backend" / "data" / "slang.json"
    pgh = root / "backend" / "data" / "pittsburgh_slang.json"
    text = "my friends like a sandwich"
    print("Demo with default mapping:")
    demo(default, text)
    print("\nDemo with Pittsburgh mapping:")
    demo(pgh, text)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
