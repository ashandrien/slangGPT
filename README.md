
# SlangGPT 

Hello local yokels, this project is a chatbot that mimics ChatGPT, but translates things into local slang.  The goal is to create extensible slang documents which you can plug-in to make the speech more localized & realistic.  I have dreams of an MCP server, but need help in modeling the correct NLP.  Thanks for visiting.

# Running the project
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

That's it — open issues or ask me to help automate these steps further (scripts, Makefile, Dockerfile adjustments, etc).
=======
## Slang GPT
A vibe-coded monstrosity with the following pieces:
* Python
* Vite
* React
