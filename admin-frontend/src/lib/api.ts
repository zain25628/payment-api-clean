import axios from 'axios'
import {
  AdminCountry,
  AdminCountryWithProviders,
  AdminCompanyListItem,
  AdminCompanyOut,
  AdminCompanyCreatePayload,
  AdminPaymentProvider,
  AdminWalletOut,
  AdminWalletCreate,
  AdminWalletUpdate
} from './types'

const client = axios.create({ baseURL: 'http://localhost:8000' })

export async function fetchCountries(): Promise<AdminCountry[]> {
  const resp = await client.get('/admin/geo/countries')
  return resp.data
}

export async function fetchCountryWithProviders(code: string): Promise<AdminCountryWithProviders> {
  const resp = await client.get(`/admin/geo/countries/${code}/providers`)
  return resp.data
}

// Payload type for creating a country. Kept local to this module so we
// don't need to modify `types.ts`. Allows additional fields if present.
type AdminCountryCreatePayload = {
  code: string
  name: string
  [key: string]: any
}

export async function createCountry(payload: AdminCountryCreatePayload): Promise<AdminCountry> {
  const resp = await client.post('/admin/geo/countries', payload)
  return resp.data
}

export async function fetchCompanyWallets(companyId: number): Promise<AdminWalletOut[]> {
  const resp = await client.get(`/admin/companies/${companyId}/wallets`)
  return resp.data
}

export async function createCompanyWallet(companyId: number, payload: AdminWalletCreate): Promise<AdminWalletOut> {
  const resp = await client.post(`/admin/companies/${companyId}/wallets`, payload)
  return resp.data
}

export async function updateWallet(walletId: number, payload: AdminWalletUpdate): Promise<AdminWalletOut> {
  const resp = await client.put(`/admin/wallets/${walletId}`, payload)
  return resp.data
}

export async function toggleWallet(walletId: number): Promise<AdminWalletOut> {
  const resp = await client.post(`/admin/wallets/${walletId}/toggle`)
  return resp.data
}

export async function fetchPaymentProviders(): Promise<AdminPaymentProvider[]> {
  const resp = await client.get('/admin/payment-providers')
  return resp.data
}

export async function createPaymentProvider(payload: {
  code: string
  name: string
  description?: string
  country_code?: string
}): Promise<AdminPaymentProvider> {
  const resp = await client.post('/admin/payment-providers', payload)
  return resp.data
}

export async function fetchCompanies(): Promise<AdminCompanyListItem[]> {
  const resp = await client.get('/admin/companies/')
  return resp.data
}

export async function createCompany(payload: AdminCompanyCreatePayload): Promise<AdminCompanyOut> {
  const resp = await client.post('/admin/companies/', payload)
  return resp.data
}

export async function getCompany(id: number): Promise<AdminCompanyOut> {
  const resp = await client.get(`/admin/companies/${id}`)
  return resp.data
}

export async function updateCompany(id: number, payload: AdminCompanyCreatePayload): Promise<AdminCompanyOut> {
  const resp = await client.put(`/admin/companies/${id}`, payload)
  return resp.data
}

export async function toggleCompany(id: number): Promise<AdminCompanyOut> {
  const resp = await client.post(`/admin/companies/${id}/toggle`)
  return resp.data
}

export async function checkHealth(): Promise<{ ok: boolean }> {
  try {
    await client.get('/health')
    return { ok: true }
  } catch (err) {
    return { ok: false }
  }
}
