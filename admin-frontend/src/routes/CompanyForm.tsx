import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { fetchCountries, fetchCountryWithProviders, createCompany, getCompany, updateCompany } from '../lib/api'
import { AdminCountry, AdminCompanyOut, AdminCompanyCreatePayload, AdminPaymentProvider } from '../lib/types'

export default function CompanyForm(){
  const { id } = useParams<{id:string}>()
  const isEdit = !!id
  const navigate = useNavigate()

  const [countries, setCountries] = useState<AdminCountry[]>([])
  const [countriesLoading, setCountriesLoading] = useState(false)
  const [providers, setProviders] = useState<AdminPaymentProvider[]>([])
  const [providersLoading, setProvidersLoading] = useState(false)
  const [companyLoading, setCompanyLoading] = useState(false)

  const [formError, setFormError] = useState<string | null>(null)
  const [errors, setErrors] = useState<{ name?: string; provider?: string; apiKey?: string }>(()=> ({}))
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [form, setForm] = useState({
    name: '',
    country_code: '',
    telegram_default_group_id: ''
  })

  const [company, setCompany] = useState<AdminCompanyOut | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [selectedProviderCodes, setSelectedProviderCodes] = useState<string[]>([])
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false)
  const [pdfLink, setPdfLink] = useState<string | null>(null)
  const [pdfError, setPdfError] = useState<string | null>(null)

  useEffect(()=>{
    setCountriesLoading(true)
    fetchCountries()
      .then(cs => setCountries(cs))
      .catch(()=> setErrorMessage('Failed to load countries'))
      .finally(()=> setCountriesLoading(false))
  },[])

  useEffect(()=>{
    // providers are loaded when a country is selected (see effect below)
  },[])

  useEffect(()=>{
    // when country_code changes, load providers for that country
    const code = form.country_code
    let mounted = true
    if(!code){
      setProviders([])
      setSelectedProviderCodes([])
      return
    }
    setProvidersLoading(true)
    fetchCountryWithProviders(code)
      .then(res => {
        if(!mounted) return
        setProviders(res.providers)
        // clear selected codes when country changes
        setSelectedProviderCodes([])
      })
      .catch(()=> {
        if(!mounted) return
        setErrorMessage('Failed to load payment providers for country')
      })
      .finally(()=> mounted && setProvidersLoading(false))

    return ()=>{ mounted = false }
  },[form.country_code])

  useEffect(()=>{
    if(isEdit && id){
      setCompanyLoading(true)
      getCompany(Number(id)).then(c=>{
        setCompany(c)
        setForm({
          name: c.name || '',
          country_code: c.country_code || '',
          telegram_default_group_id: c.telegram_default_group_id || ''
        })
        // load providers for the company's country and preselect provider codes
        const countryCode = c.country_code
        const existing = c.channels?.map(ch => ch.provider_code).filter(Boolean) as string[]
        if(countryCode){
          fetchCountryWithProviders(countryCode).then(res => {
            setProviders(res.providers)
            if(existing && existing.length) setSelectedProviderCodes(existing)
          }).catch(()=> setErrorMessage('Failed to load payment providers for company country'))
        } else {
          if(existing && existing.length) setSelectedProviderCodes(existing)
        }
      }).catch((err:any)=> setErrorMessage('Failed to load company'))
      .finally(()=> setCompanyLoading(false))
    }
  },[id, isEdit])

  function onChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>){
    const { name, value } = e.target
    setForm(s => ({ ...s, [name]: value }))
    if(name === 'name' && value.trim()) setErrors(f=> ({...f, name: undefined}))
  }

  function toggleProvider(code: string){
    setErrors(f=> ({...f, provider: undefined}))
    setSelectedProviderCodes(prev => {
      if(prev.includes(code)) return prev.filter(p => p !== code)
      return [...prev, code]
    })
  }

  function selectAllProviders(){
    setErrors(f=> ({...f, provider: undefined}))
    setSelectedProviderCodes(providers.map(p=>p.code))
  }

  function clearAllProviders(){
    setErrors(f=> ({...f, provider: undefined}))
    setSelectedProviderCodes([])
  }

  async function onSubmit(e: React.FormEvent){
    e.preventDefault()
    setErrorMessage(null)
    setFormError(null)

    const newErrors: { name?: string; provider?: string; apiKey?: string } = {}
    if(!form.name || !form.name.trim()) newErrors.name = 'Company name is required'
    if(!selectedProviderCodes || selectedProviderCodes.length === 0) newErrors.provider = 'Select at least one provider'

    // optional: validate apiKey/callback if present on the form object
    const maybeApiKey = (form as any).api_key ?? (form as any).apiKey
    if(typeof maybeApiKey !== 'undefined'){
      if(!maybeApiKey || String(maybeApiKey).trim() === '') newErrors.apiKey = 'API key is required'
    }

    if(Object.keys(newErrors).length){
      setErrors(newErrors)
      return
    }

    setErrors({})
    setIsSubmitting(true)

    const payload: AdminCompanyCreatePayload = {
      name: form.name.trim(),
      country_code: form.country_code || undefined,
      telegram_default_group_id: form.telegram_default_group_id || undefined
      ,provider_codes: selectedProviderCodes
    }

    try{
      if(isEdit && id){
        const updated = await updateCompany(Number(id), payload)
        setCompany(updated)
      } else {
        const created = await createCompany(payload)
        setCompany(created)
      }
      setSuccessMessage('Company saved')
      setTimeout(()=> navigate('/companies'), 700)
    }catch(err:any){
      const axiosErr = err as any
      const detail =
        axiosErr?.response?.data?.detail ||
        axiosErr?.response?.statusText ||
        axiosErr?.message ||
        'Failed to save company'
      setFormError(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }finally{
      setIsSubmitting(false)
    }
  }

  async function handleGenerateOnboardingPdf(){
    if(!company) return
    setIsGeneratingPdf(true)
    setPdfError(null)
    setPdfLink(null)
    try{
      const res = await fetch(`http://localhost:8000/admin/companies/${company.id}/onboarding-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if(!res.ok){
        const txt = await res.text()
        throw new Error(txt || `Request failed: ${res.status}`)
      }
      const data = await res.json()
      if(data.download_url){
        setPdfLink(data.download_url)
      } else if(data.html_path){
        setPdfError('PDF not available; use server-side HTML to print to PDF.')
      } else {
        setPdfError('Unexpected response from server')
      }
    }catch(err:any){
      setPdfError(err?.message || 'Failed to generate PDF')
    }finally{
      setIsGeneratingPdf(false)
    }
  }

  // Quick integration snippets as string constants so JSX doesn't try to parse
  // the example code as real TSX/JS objects.
  const jsSnippet = `function requestWallet(preferredPaymentMethod) {
  return fetch("http://localhost:8000/wallets/request", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': '${company?.api_key ?? "<MERCHANT_API_KEY>"}',
    },
    body: JSON.stringify({
      amount: 100,
      currency: 'AED',
      txn_id: 'ORDER-123',
      payer_phone: '+971500000000',
      // optional: choose provider per button
      preferred_payment_method: preferredPaymentMethod,
    }),
  }).then(r => r.json());
}

// Example buttons:
// <button onclick="requestWallet('eand_money')">Pay with e& money</button>
// <button onclick="requestWallet('stripe')">Pay with Stripe</button>
// <button onclick="requestWallet('ui-test')">Pay with UI Test Provider</button>`;

  const pythonSnippet = `import os
import requests

BASE_URL = os.getenv("PAYMENT_GATEWAY_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("MERCHANT_API_KEY", "${company?.api_key ?? '<YOUR_MERCHANT_API_KEY>'}")

resp = requests.post(
    f"{BASE_URL}/wallets/request",
    headers={"X-API-Key": API_KEY},
    json={
        "amount": 100,
        "currency": "AED",
        "txn_id": "ORDER-123",
        "payer_phone": "+971500000000",
        # optional: pass preferred_payment_method to restrict wallet selection
        # "preferred_payment_method": "eand_money",
    },
)
print(resp.status_code, resp.json())`;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-bold mb-1">{isEdit ? 'Edit Company' : 'Create Company'}</h1>
          <p className="text-sm text-gray-600 mb-4">Create or update a company and configure supported payment providers.</p>

          {(countriesLoading || companyLoading) && (
            <div className="mb-4 text-sm text-gray-600">Loading...</div>
          )}

          {errorMessage && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-100 rounded">{errorMessage}</div>
          )}
          {formError && (
            <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
          )}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-50 text-green-700 border border-green-100 rounded">{successMessage}</div>
          )}

          <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">Name</label>
                <input name="name" value={form.name} onChange={onChange} className="mt-1 block w-full border rounded p-2" />
                {errors.name && <div className="text-red-600 text-sm mt-1">{errors.name}</div>}
              </div>

              <div>
                <label className="block text-sm font-medium">Country</label>
                <select name="country_code" value={form.country_code} onChange={onChange} className="mt-1 block w-full border rounded p-2" disabled={countriesLoading}>
                  <option value="">Select country</option>
                  {countries.map(c=> <option key={c.id} value={c.code}>{c.name}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium">Telegram Default Group ID</label>
                <input name="telegram_default_group_id" value={form.telegram_default_group_id} onChange={onChange} className="mt-1 block w-full border rounded p-2" />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium">Supported Payment Providers</label>
                <div className="mt-2 mb-2 flex gap-2">
                  <button type="button" onClick={selectAllProviders} className="text-sm text-blue-600">Select all</button>
                  <button type="button" onClick={clearAllProviders} className="text-sm text-gray-600">Clear all</button>
                </div>
                {providersLoading ? (
                  <div className="text-sm text-gray-600">Loading providers...</div>
                ) : (
                  <div className="grid grid-cols-1 gap-2 max-h-64 overflow-auto">
                    {providers.map(p => (
                      <label key={p.id} className="inline-flex items-center gap-2">
                        <input type="checkbox" checked={selectedProviderCodes.includes(p.code)} onChange={()=> toggleProvider(p.code)} />
                        <span className="text-sm">{p.name} ({p.code})</span>
                      </label>
                    ))}
                  </div>
                )}
                {errors.provider && <div className="text-red-600 text-sm mt-1">{errors.provider}</div>}
                {!providersLoading && providers.length === 0 && <div className="text-sm text-gray-600 mt-1">No payment providers available.</div>}
              </div>
            </div>

            <div className="md:col-span-2 flex items-center gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded w-full md:w-auto" disabled={isSubmitting || countriesLoading || companyLoading}>
                {isSubmitting ? 'Saving...' : (isEdit ? 'Update company' : 'Create company')}
              </button>
              <button type="button" onClick={()=> navigate('/companies')} className="px-4 py-2 border rounded bg-gray-50">Cancel</button>
            </div>
          </form>

          {company && (
            <div className="bg-gray-50 p-4 rounded mt-6">
              <h2 className="font-semibold">Result</h2>
              <div className="mt-2">API key: <code className="bg-white px-2 py-1 rounded">{company.api_key ?? '—'}</code></div>
              {company.channels && company.channels.length > 0 && (
                <div className="mt-2">Channel API key: <code className="bg-white px-2 py-1 rounded">{company.channels[0].channel_api_key ?? '—'}</code></div>
              )}
              {company.wallets && company.wallets.length > 0 && (
                <div className="mt-2">Default wallet: <code className="bg-white px-2 py-1 rounded">{company.wallets[0].wallet_identifier ?? '—'}</code></div>
              )}

              <div className="mt-4">
                <button
                  type="button"
                  onClick={handleGenerateOnboardingPdf}
                  disabled={!company || isGeneratingPdf}
                  className="inline-flex items-center rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-60"
                >
                  {isGeneratingPdf ? 'Generating PDF...' : 'Generate onboarding PDF'}
                </button>

                {pdfLink && (
                  <a href={pdfLink} target="_blank" rel="noreferrer" className="ml-3 text-sm text-blue-600 hover:underline">Download latest PDF</a>
                )}

                {pdfError && (
                  <div className="mt-2 text-sm text-red-600">{pdfError}</div>
                )}
              </div>

              <div className="mt-4">
                <h3 className="font-medium">Quick integration snippet</h3>
                <p className="text-sm text-gray-600 mb-2">Use this snippet to request a wallet/payment destination from the gateway. Replace the placeholders with your environment values and keep your API key secret (store it in an environment variable).</p>

                <div className="mb-3">
                  <div className="text-sm font-medium mb-1">JavaScript (fetch)</div>
                  <pre className="bg-black text-white text-sm p-3 rounded overflow-auto"><code>{jsSnippet}</code></pre>
                </div>

                <div>
                  <div className="text-sm font-medium mb-1">Python (requests)</div>
                  <pre className="bg-black text-white text-sm p-3 rounded overflow-auto"><code>{pythonSnippet}</code></pre>
                </div>

                <p className="text-xs text-gray-500 mt-2">Note: <strong>BASE_URL</strong> depends on your environment (dev/staging/prod). Use the values from your deployment or `http://localhost:8000` for local development. Do not hard-code your API key in browser/client code — keep it on your server or in environment variables.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
