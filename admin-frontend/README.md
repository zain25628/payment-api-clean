# Admin Frontend

## Prerequisites

- Install Node.js LTS (Node 18 or newer recommended).
- Download Node.js (LTS) from: https://nodejs.org

After installing Node.js, run the following to start the dev server:

```powershell
cd admin-frontend
npm install
npm run dev
```

This project uses Vite as the dev server (default port 5173).

This is a small React + TypeScript + Vite + Tailwind admin UI for managing companies and geo/providers.

Quick start (from `admin-frontend/`):

```powershell
# install deps
npm install

<!--
Quick run notes (auto-generated):
- How to run: from `admin-frontend/` run `npm install` then `npm run dev`.
- Script used for dev: `dev: "vite"` (Vite dev server).
- Recommended Node: not explicitly specified in package.json; use Node 18+ (current Vite/React toolchain).
- Expected local URL: http://localhost:5173 (configured in `vite.config.mts`).
-->

# start dev server
npm run dev
```

The UI expects the backend to be reachable at `http://localhost:8000` and will call the admin endpoints documented in the repo.

Notes:
- This is a minimal PoC admin UI. No auth is configured.
- If you want to build production assets: `npm run build` and `npm run preview` to check the built app.

## Troubleshooting

### 'node' or 'npm' is not recognized
- Make sure Node.js LTS is installed from https://nodejs.org (choose the LTS version).
- After installation, completely close and reopen VS Code so the updated PATH is loaded.
- In a new VS Code terminal run:
	```powershell
	cd C:\Users\zaink\OneDrive\Desktop\api\admin-frontend
	node -v
	npm -v
	```

If versions appear (e.g. v18.x.x and 9.x.x), then install dependencies and start the dev server:

```powershell
npm install
npm run dev
```

If the commands are still not recognized, restart Windows, then retry the steps above.

## Backend & docs

This admin frontend is designed to work with the FastAPI backend in the
project root.

- See `../README.md` for backend setup and the local end-to-end demo
	(`dev_seed.py`, `create_test_payment.py`, `merchant_demo.py`).
- See `../CHANGELOG.md` for recent changes to the backend and tooling.
