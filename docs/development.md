# Development

Install Python dependencies with `pip install -r requirements.txt` and run
`python -m pytest -q`. Compile the backend with `python -m compileall backend`.
Run the dashboard from `frontend` with `npm ci`, `npm run lint`, and `npm run
build`.

Use `backend/.env` for local secrets. Commit only `.env.example` templates.
Generated databases, caches, virtual environments, `node_modules`, and Next.js
build output are ignored.
