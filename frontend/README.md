# Frontend (Vite + React)

Development

- Start the dev server:

```bash
cd frontend
npm install
npm run dev
```

- The project uses a Vite dev proxy (`vite.config.ts`) that forwards API requests for `/slang` and `/chat` to the backend at `http://127.0.0.1:8000`. This means the frontend can use relative fetch paths (e.g. `fetch('/slang')`) during development without CORS issues.

Production

- The production build outputs to `dist/`. Serve `dist/` from a static host or a reverse proxy that also forwards `/slang` to your backend.
