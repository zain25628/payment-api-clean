# Admin Frontend

This is a small React + TypeScript + Vite + Tailwind admin UI for managing companies and geo/providers.

Quick start (from `admin-frontend/`):

```powershell
# install deps
npm install

# start dev server
npm run dev
```

The UI expects the backend to be reachable at `http://localhost:8000` and will call the admin endpoints documented in the repo.

Notes:
- This is a minimal PoC admin UI. No auth is configured.
- If you want to build production assets: `npm run build` and `npm run preview` to check the built app.
