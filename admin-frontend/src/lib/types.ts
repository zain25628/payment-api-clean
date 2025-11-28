export type AdminCountry = {
  id: number
  code: string
  name: string
}

export type AdminPaymentProvider = {
  id: number
  code: string
  name: string
  description?: string | null
  country_code?: string | null
}

export type AdminCountryWithProviders = {
  country: AdminCountry
  providers: AdminPaymentProvider[]
}

export type AdminChannelOut = {
  id: number
  name: string
  provider_code: string
  channel_api_key?: string | null
  is_active: boolean
}

export type AdminCompanyListItem = {
  id: number
  name: string
  country_code?: string | null
  is_active: boolean
}

export type AdminCompanyOut = {
  id: number
  name: string
  api_key?: string | null
  country_code?: string | null
  telegram_bot_token?: string | null
  telegram_default_group_id?: string | null
  is_active: boolean
  channels: AdminChannelOut[]
}

export type AdminCompanyCreatePayload = {
  name: string
  country_code?: string | null
  telegram_bot_token?: string | null
  telegram_default_group_id?: string | null
  provider_codes?: string[]
}

// Admin wallet types: used by the admin UI to display and manage wallets.
// These mirror the backend admin wallet schema exposed by `/admin/companies/{id}/wallets`.
export type AdminWalletOut = {
  id: number
  company_id: number
  channel_id: number | null
  wallet_label: string
  wallet_identifier: string
  daily_limit: number | null
  is_active: boolean
  channel_name?: string | null
  provider_code?: string | null
  provider_name?: string | null
  created_at?: string | null
  updated_at?: string | null
}

// Payload sent when creating a new wallet for a company.
export type AdminWalletCreate = {
  channel_id: number
  wallet_label: string
  wallet_identifier: string
  daily_limit?: number | null
  is_active?: boolean
}

// Payload for updating an existing wallet; all fields optional.
export type AdminWalletUpdate = {
  wallet_label?: string | null
  wallet_identifier?: string | null
  daily_limit?: number | null
  is_active?: boolean | null
}
