# Admin Wallets Router

Routes added for admin management of wallets:

- `GET /admin/companies/{company_id}/wallets` — list wallets for a company (returns `AdminWalletOut` list).
- `POST /admin/companies/{company_id}/wallets` — create a wallet for a company (body: `AdminWalletCreate`).
- `PUT /admin/wallets/{wallet_id}` — update wallet fields (body: `AdminWalletUpdate`).
- `POST /admin/wallets/{wallet_id}/toggle` — flip `is_active` for a wallet.

Usage: the admin UI should call the company list endpoint, let operator select a company, then list/create/update wallets.
