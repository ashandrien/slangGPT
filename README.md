# SlangGPT — Local development README

This README shows how to run the SlangGPT app locally (backend + frontend) without Docker.

Quick start (dev)

1) Backend (Python 3.11 recommended)

```bash
# from repository root
cd backend
# create a venv if you haven't already
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# copy .env.example -> .env and edit (set OPENAI_API_KEY if you want OpenAI)
cp .env.example .env
# edit backend/.env and set OPENAI_API_KEY and OPENAI_MODEL if desired

# install spaCy model (if not already installed)
python -m pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0-py3-none-any.whl

# start backend
. .venv/bin/activate
nohup .venv/bin/uvicorn main:app --reload --port 8000 > uvicorn.log 2>&1 &

# tail logs to verify
tail -n 200 uvicorn.log
```

2) Frontend (Node 18+ recommended)

```bash
cd frontend
npm install
# start Vite dev server (it proxies API calls to backend during dev)
./node_modules/.bin/vite --host 127.0.0.1 --port 5173
# open http://127.0.0.1:5173 in your browser
```

What the dev server proxies to the backend
- `/slang` -> backend `/slang`
- `/chat` -> backend `/chat`
- `/openai_slang` -> backend `/openai_slang`
- `/reload_slang` -> backend `/reload_slang`

Troubleshooting notes
- If spaCy import fails with native build errors on macOS, use Python 3.11 (Homebrew) and prefer binary wheels. See backend/requirements.txt for pinned versions.
- If you see `ValueError: numpy.dtype size changed`, uninstall/reinstall `numpy` first then reinstall spaCy-related packages so compiled extensions match your numpy ABI.
- If frontend requests return 404, ensure the Vite dev server proxy is running and points to `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).
- If OpenAI calls return errors, confirm `OPENAI_API_KEY` is set in `backend/.env` and restart the backend so load_dotenv picks it up.

Custom slang mapping
--------------------
The backend loads a mapping from `backend/data/slang.json` by default. You can provide your own mapping file by setting `SLANG_FILE` in `backend/.env` (absolute path or relative to the `backend/` folder). The mapping should be a JSON object where keys are lowercase source words/phrases and values are either a single replacement string or a list of replacement strings.

One-command dev starter

- A convenience script and Makefile target were added to start both servers with one command:

	- `make start-dev` (from repo root)
	- or `./scripts/start-dev.sh`

- What the script does:
	- creates a Python 3.11 venv at `backend/.venv` if missing (uses Homebrew python at `/opt/homebrew/opt/python@3.11/bin/python3.11` — update the script if your python is elsewhere).
	- installs backend requirements if venv is created.
	- copies `backend/.env.example` -> `backend/.env` if `.env` is missing (it won't overwrite an existing `.env`).
	- starts `uvicorn main:app --reload --port 8000` in the background and writes logs to `backend/uvicorn.log`.
	- runs `npm install` in `frontend/` if `node_modules` is missing and starts Vite on `127.0.0.1:5173`, writing logs to `frontend/vite.log`.
	- tails the last 20 lines of both logs for quick verification.

Using custom fonts for headings

If you have custom font files you want to use for `h1` headings, place them in `frontend/public/assets/fonts/` with names like `MyFont-Regular.woff2` and `MyFont-Bold.woff2`. The app's stylesheet already includes @font-face rules that load these files and applies the font to `.app-header h1`.

Example (from repo root):

```bash
mkdir -p frontend/public/assets/fonts
cp /path/to/your/MyFont-Regular.woff2 frontend/public/assets/fonts/
cp /path/to/your/MyFont-Bold.woff2 frontend/public/assets/fonts/
```

If your font files use different names or you're using variable fonts, update `frontend/src/styles.css` to point to the correct filenames and font-family name.

Stopping servers

- The start script currently skips starting servers if it sees matching processes already running. To stop servers manually:

```bash
# stop uvicorn (example: find the PID and kill)
pgrep -f "uvicorn.*main:app" | xargs -r kill -9

# stop Vite
pgrep -f "node .*node_modules/.bin/vite" | xargs -r kill -9
```

If you'd like, I can add `make stop-dev` to automate stopping both.

Security
- Keep `.env` out of source control. Do not commit API keys.

Observability (Honeycomb)
-------------------------
If you'd like to send traces to Honeycomb, set the following environment variables in `backend/.env` (do NOT commit real keys):

```
HONEYCOMB_API_KEY=key-REPLACE_ME
HONEYCOMB_DATASET=slanggpt-backend
```

The backend will attempt to initialize Honeycomb via the `beeline` library if `HONEYCOMB_API_KEY` is present. We intentionally make this optional so the app runs without Honeycomb configured.

That's it — open issues or ask me to help automate these steps further (scripts, Makefile, Dockerfile adjustments, etc).

Contributing slang mappings
---------------------------
We welcome contributions that add or improve local slang mappings. Below are quick guidelines so contributions are consistent and easy to review.

1) File format

- The mapping file is a JSON object. Keys are lowercase source words or short phrases (e.g. "sandwich", "you all").
- Values may be a single replacement string or a list of replacement strings to allow randomization in the output. Example:

```json
{
	"sandwich": ["primanti", "hoagie"],
	"friend": "nebby"
}
```

2) Validation

- Before creating a pull request, run the validator to catch syntax or shape problems:

```bash
python3 scripts/validate_slang.py backend/data/pittsburgh_slang.json
# or your new file path
```

The validator checks that the top-level value is an object and that every value is a string or list of strings. It exits non-zero on problems.

3) Testing locally

- Try the demo script to quickly see how the mapping changes conversion results (no spaCy required):

```bash
python3 scripts/demo_swap_slang.py
```

- To run the backend server with your mapping, set `SLANG_FILE` in `backend/.env` (absolute path or path relative to `backend/`) and restart the server. Example:

```bash
echo "SLANG_FILE=backend/data/pittsburgh_slang.json" >> backend/.env
# restart uvicorn
```

4) PR checklist for mapping changes

- [ ] Run `python3 scripts/validate_slang.py <path-to-file>` and ensure it reports OK.
- [ ] Include a short description in the PR explaining the region/context for the mapping.
- [ ] Keep mappings focused and avoid offensive or abusive terms. The project maintainers reserve the right to refuse or sanitize submissions that contain harmful content.
- [ ] Add a small example or test line in the PR description showing an input and expected converted output.

If you'd like, I can add a GitHub Actions job that runs `scripts/validate_slang.py` on PRs to automatically block malformed mappings from being merged.
