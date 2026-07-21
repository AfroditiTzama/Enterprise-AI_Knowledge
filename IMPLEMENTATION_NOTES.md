# UX & Reliability Pass

This package contains the updated `apps/api` and `apps/web` trees for the
Enterprise AI Knowledge Assistant.

## Included fixes and features

- Reactive authentication state: sign-out and sign-in work without a hard refresh.
- Correct login, expired-session and API error messages.
- Automatic retries for temporary network/5xx failures and a visible Retry action.
- Clear loading, retrying, error, empty and success states.
- Wiki empty state is no longer shown when the request failed.
- Knowledge Graph reset restores nodes, pan, zoom and search state.
- Light, Dark and System appearance modes saved in local storage.
- Calmer visual system, responsive navigation and improved spacing/contrast.
- Assistant introduction, suggested questions and clearer relevance labels.
- My Profile page with account details, workspace statistics and appearance controls.
- Document deletion with confirmation, file/chunk/vector cleanup and ownership checks.

## Local validation performed in the sandbox

- Frontend production build passed with `npm run build`.
- Python source and tests passed bytecode compilation.
- Delete-document command smoke test passed.

The full backend pytest suite must still be run in the project's Python 3.12
virtual environment because the sandbox does not contain the project's complete
Python dependency environment.

## Apply to the local repository

Extract this archive over the repository root so that the included `apps/`
folder replaces the matching files. Review with:

```bash
cd /Users/afrodititzama/Desktop/enterprise-ai-knowledge-assistant
git status --short
git diff --check
```

## Validate locally

Backend:

```bash
cd /Users/afrodititzama/Desktop/enterprise-ai-knowledge-assistant/apps/api
source .venv/bin/activate
set -a
source .env
set +a
pytest -q
python -m uvicorn knowledge_assistant.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Frontend, in a second terminal:

```bash
cd /Users/afrodititzama/Desktop/enterprise-ai-knowledge-assistant/apps/web
npm install
npm run build
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`.
