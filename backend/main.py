from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
import re
from slang import convert_to_philly_slang
from slang import reload_slang_mapping, SLANG_MAP
import os
import openai
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env if present (local dev convenience). Keep .env out of VCS.
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=str(_env_path))
import logging

# Honeycomb / Beeline optional integration
HONEYCOMB_API_KEY = os.getenv("HONEYCOMB_API_KEY")
HONEYCOMB_DATASET = os.getenv("HONEYCOMB_DATASET", "slanggpt-backend")
HONEYCOMB_ENABLED = False
try:
    if HONEYCOMB_API_KEY:
        import beeline

        beeline.init(writekey=HONEYCOMB_API_KEY, dataset=HONEYCOMB_DATASET, service_name="slanggpt-backend")
        HONEYCOMB_ENABLED = True
except Exception as e:
    # don't fail startup if beeline isn't available or initialization fails
    HONEYCOMB_ENABLED = False
    # defer logging setup until logger exists
    try:
        print(f"Honeycomb init failed or not configured: {e}")
    except Exception:
        pass


app = FastAPI(title="phillygpt-backend")

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phillygpt")
if HONEYCOMB_ENABLED:
    logger.info(f"Honeycomb beeline initialized (dataset={HONEYCOMB_DATASET})")
else:
    logger.info("Honeycomb not enabled")

# --- Safety limits and sanitization -------------------------------------------------
# Maximum request body (bytes) we'll accept without returning 413
MAX_CONTENT_LENGTH = 200_000  # ~200 KB
# Maximum characters we'll pass into NLP/conversion routines
MAX_TEXT_LENGTH = 10_000


@app.middleware("http")
async def limit_content_length(request: Request, call_next):
    """Reject requests that advertise an excessively large Content-Length.

    Note: this relies on the client sending Content-Length. For chunked
    requests the server will still be protected by nginx's client_max_body_size
    and by downstream memory/time limits.
    """
    cl = request.headers.get("content-length")
    if cl:
        try:
            n = int(cl)
        except Exception:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})
        if n > MAX_CONTENT_LENGTH:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})
    return await call_next(request)


# Optional Honeycomb trace middleware (non-fatal if beeline isn't available)
if HONEYCOMB_ENABLED:
    try:
        import beeline as _beeline

        @app.middleware("http")
        async def beeline_middleware(request: Request, call_next):
            try:
                # Add some useful context fields for every request
                _beeline.add_context_field("http.method", request.method)
                _beeline.add_context_field("http.path", request.url.path)
                _beeline.add_context_field("client.ip", request.client.host if request.client else "")
                _beeline.start_trace()
            except Exception:
                pass
            try:
                response = await call_next(request)
                return response
            finally:
                try:
                    _beeline.end_trace()
                except Exception:
                    pass
    except Exception:
        # If importing beeline fails, skip middleware silently
        pass


def sanitize_text(s: str, max_chars: int = MAX_TEXT_LENGTH) -> str:
    """Sanitize incoming text to avoid problematic control characters and
    extremely long payloads. This is defensive: it removes null bytes and
    most ASCII control characters while preserving common whitespace.
    """
    if s is None:
        return ""
    if not isinstance(s, str):
        try:
            s = str(s)
        except Exception:
            s = ""
    # Remove NUL bytes and control characters except newline, carriage return and tab
    s = s.replace("\x00", "")
    s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    s = s.strip()
    if len(s) > max_chars:
        s = s[:max_chars]
    return s



def _call_openai_chat(prompt: str):
    """Compatibility wrapper for different openai-python versions.

    Tries the legacy `openai.ChatCompletion.create(...)` first (older
    clients). If that fails with the v1 API removal, falls back to the new
    client interface `OpenAI().chat.completions.create(...)`.

    Returns (assistant_text, error_str). If successful, error_str is None.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # Try legacy API first for compatibility
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.7,
        )
        # legacy response shape
        assistant_text = resp.choices[0].message.content.strip()
        return assistant_text, None
    except Exception as e_legacy:
        # Try new OpenAI client API (openai>=1.0.0)
        try:
            # Import inside function so it's optional at module import time
            from openai import OpenAI as OpenAIClient

            client = OpenAIClient(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.7,
            )
            # New client mirrors the same structure for choices/message
            assistant_text = None
            if getattr(resp, "choices", None):
                choice0 = resp.choices[0]
                # some SDK versions nest message/content differently
                if getattr(choice0, "message", None) and getattr(choice0.message, "content", None):
                    assistant_text = choice0.message.content
                elif isinstance(choice0, dict) and choice0.get("message"):
                    assistant_text = choice0["message"].get("content", "")
                else:
                    # fallback printing the entire choice as string
                    assistant_text = str(choice0)

            assistant_text = (assistant_text or "").strip()
            return assistant_text, None
        except Exception as e_new:
            # Return the original legacy exception if that's most informative
            return "", f"legacy_error={e_legacy}; new_error={e_new}"

# Allow configuring allowed origins via environment variable for easy local
# adjustments without changing code. Provide a comma-separated list, e.g.
# ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
env_allowed = os.getenv("ALLOWED_ORIGINS")
if env_allowed:
    allowed_origins = [o.strip() for o in env_allowed.split(",") if o.strip()]
else:
    # Default dev-safe origins
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5178",
        "http://127.0.0.1:5178",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    meta: dict


class SlangRequest(BaseModel):
    text: str


class SlangResponse(BaseModel):
    converted: str


class OpenAIRequest(BaseModel):
    prompt: str


class OpenAIResponse(BaseModel):
    original: str
    converted: str


@app.on_event("startup")
def load_spacy_model():
    # Uses en_core_web_sm by default. Install with: python -m spacy download en_core_web_sm
    global nlp
    try:
        # Import spaCy lazily so the app can start even if the library or model
        # isn't available (useful for development where installing spaCy can
        # be heavy or require a different Python runtime). If import or model
        # loading fails we keep `nlp` as None and log a warning.
        import spacy

        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        # Don't raise — allow the app to start. Endpoints that need spaCy
        # will return a helpful error message instead.
        nlp = None
        logger.warning(
            "spaCy not available or model not installed; NLP endpoints will be disabled: %s",
            str(e),
        )
    # Log whether optional integrations are configured (without revealing secrets)
    openai_present = bool(os.getenv("OPENAI_API_KEY"))
    openai_model = os.getenv("OPENAI_MODEL")
    logger.info(f"spaCy loaded. OpenAI configured: {openai_present}. OpenAI model: {openai_model}")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        if "nlp" not in globals() or globals().get("nlp") is None:
            raise HTTPException(status_code=503, detail="spaCy not loaded. Install the model with: python -m spacy download en_core_web_sm")

        message = sanitize_text(req.message)
        if not message:
            raise HTTPException(status_code=400, detail="Empty message")

        doc = nlp(message)

        entities = [(ent.text, ent.label_) for ent in doc.ents]
        nouns = [chunk.text for chunk in doc.noun_chunks]

        reply_lines = []
        if entities:
            reply_lines.append(f"I detected these entities: {entities}.")
        if nouns:
            reply_lines.append(f"Key noun phrases: {nouns}.")

        if not reply_lines:
            reply_lines.append("Thanks — I parsed your message but didn't find named entities or noun chunks to highlight.")

        reply_lines.append("(This reply is generated by a simple spaCy-based pipeline; replace with your model logic.)")

        meta = {"entity_count": len(entities), "noun_chunks_count": len(nouns)}
        return ChatResponse(reply="\n".join(reply_lines), meta=meta)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in /chat: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/slang", response_model=SlangResponse)
def slang(req: SlangRequest):
    """Return a Philly-slang converted version of the input text."""
    try:
        if "nlp" not in globals() or globals().get("nlp") is None:
            raise HTTPException(status_code=503, detail="spaCy not loaded. Install the model with: python -m spacy download en_core_web_sm")

        text = sanitize_text(req.text)
        if not text:
            raise HTTPException(status_code=400, detail="Empty text")

        converted = convert_to_philly_slang(nlp, text)
        return SlangResponse(converted=converted)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in /slang: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/openai_slang", response_model=OpenAIResponse)
def openai_slang(req: OpenAIRequest):
    """Send a prompt to OpenAI and return the assistant reply plus a slangified
    version of the assistant reply.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    # Friendly fallback message to display when OpenAI can't provide a reply
    fallback_msg = "I'm out of tokens - buy my album"

    if not api_key:
        # No API key — still return the fallback so the frontend displays it.
        converted = ""
        if "nlp" in globals() and globals().get("nlp") is not None:
            try:
                converted = convert_to_philly_slang(nlp, fallback_msg)
            except Exception:
                converted = ""
        return OpenAIResponse(original=fallback_msg, converted=converted)

    openai.api_key = api_key
    try:
        prompt = sanitize_text(req.prompt)
        if not prompt:
            raise HTTPException(status_code=400, detail="Empty prompt")

        assistant_text, err = _call_openai_chat(prompt)
        if err or not assistant_text:
            # If OpenAI call failed or returned no text, show the playful fallback message
            logger.warning("OpenAI call failed or empty response: %s", err)
            assistant_text = fallback_msg

        # Convert assistant reply to Philly slang if spaCy is available; otherwise return empty converted
        converted = ""
        if "nlp" in globals() and globals().get("nlp") is not None:
            try:
                converted = convert_to_philly_slang(nlp, assistant_text)
            except Exception as e:
                logger.warning("Failed to convert assistant reply to slang: %s", e)
                converted = ""

        return OpenAIResponse(original=assistant_text, converted=converted)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled exception while calling OpenAI: %s", e)
        converted = ""
        if "nlp" in globals() and globals().get("nlp") is not None:
            try:
                converted = convert_to_philly_slang(nlp, fallback_msg)
            except Exception:
                converted = ""
        return OpenAIResponse(original=fallback_msg, converted=converted)


# If a `static` directory exists inside the backend folder (populated by the
# frontend build), serve it under `/static` so API routes (for example
# `/health`) are not shadowed by the static file mount during local dev.
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.exists():
    # Serve built assets at /static/...; in production you can reverse-proxy
    # or adjust this if you prefer the frontend to be served at root.
    app.mount("/static", StaticFiles(directory=str(_static_dir), html=True), name="static")


@app.post("/reload_slang")
def reload_slang():
    """Force-reload the philly_slang.json file from disk.

    This is useful in development so edits to the JSON file take effect
    immediately without restarting the server.
    """
    try:
        reload_slang_mapping()
        return {"ok": True, "entries": len(SLANG_MAP)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/slang_files")
def list_slang_files(request: Request):
    """Return a list of available slang JSON files under backend/data.

    For safety this only allows listing files from the backend/data directory.
    """
    try:
        base = Path(__file__).resolve().parent / "data"
        files = [p.name for p in base.glob("*.json") if p.is_file()]
        return {"ok": True, "files": files}
    except Exception as e:
        logger.exception("Failed to list slang files: %s", e)
        return {"ok": False, "error": str(e)}


class SetSlang(BaseModel):
    filename: str


@app.post("/set_slang_file")
def set_slang_file_endpoint(req: SetSlang, request: Request):
    """Set the active slang file (local/dev use only).

    This endpoint accepts a filename (not a path) that must exist under
    backend/data. For safety it only accepts requests from localhost.
    """
    client = request.client.host if request.client is not None else None
    if client not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        from slang import set_slang_file

        ok = set_slang_file(req.filename)
        if not ok:
            raise HTTPException(status_code=400, detail="Invalid filename or not allowed")
        return {"ok": True, "filename": req.filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to set slang file: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Return a small health JSON describing optional integrations.

    - openai_configured: whether an OPENAI_API_KEY is present
    - spacy_loaded: whether spaCy model appears to be importable (True if the
        global `nlp` exists)
    - slang_entries: number of entries in the configured slang mapping
    """
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    spacy_loaded = "nlp" in globals() and globals().get("nlp") is not None
    slang_entries = len(SLANG_MAP) if isinstance(SLANG_MAP, dict) else 0
    return {
        "ok": True,
        "openai_configured": openai_configured,
        "openai_model": os.getenv("OPENAI_MODEL"),
        "spacy_loaded": spacy_loaded,
        "slang_entries": slang_entries,
    }


@app.get("/observability_status")
def observability_status():
    """Return a small observability status useful for debugging Honeycomb setup.

    Fields:
    - honeycomb_enabled: whether beeline was initialized successfully
    - honeycomb_dataset: configured dataset name
    - honeycomb_api_key_present: whether an API key is set in env
    - slang_entries: number of entries in the configured slang mapping
    - active_slang_file: resolved path to the currently-loaded slang JSON (if available)
    """
    # active slang file is tracked in the slang module's _data_path variable
    active_file = None
    try:
        import importlib

        slang_mod = importlib.import_module("slang")
        dp = getattr(slang_mod, "_data_path", None)
        if dp is not None:
            try:
                active_file = str(dp)
            except Exception:
                active_file = repr(dp)
    except Exception:
        active_file = None

    return {
        "honeycomb_enabled": bool(globals().get("HONEYCOMB_ENABLED", False)),
        "honeycomb_dataset": globals().get("HONEYCOMB_DATASET"),
        "honeycomb_api_key_present": bool(os.getenv("HONEYCOMB_API_KEY")),
        "slang_entries": len(SLANG_MAP) if isinstance(SLANG_MAP, dict) else 0,
        "active_slang_file": active_file,
    }

