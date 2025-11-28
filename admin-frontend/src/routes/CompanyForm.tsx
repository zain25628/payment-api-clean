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
  const [saving, setSaving] = useState(false)

  const [form, setForm] = useState({
    name: '',
    country_code: '',
    telegram_default_group_id: ''
  })

  const [company, setCompany] = useState<AdminCompanyOut | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [fieldError, setFieldError] = useState<{name?:string}>({})
  const [selectedProviderCodes, setSelectedProviderCodes] = useState<string[]>([])
  // extend fieldError to include providers
  const [providersFieldError, setProvidersFieldError] = useState<string | undefined>()

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
    if(name === 'name' && value.trim()) setFieldError(f=> ({...f, name: undefined}))
  }

  function toggleProvider(code: string){
    setProvidersFieldError(undefined)
    setSelectedProviderCodes(prev => {
      if(prev.includes(code)) return prev.filter(p => p !== code)
      return [...prev, code]
    })
  }

  function selectAllProviders(){
    setProvidersFieldError(undefined)
    setSelectedProviderCodes(providers.map(p=>p.code))
  }

  function clearAllProviders(){
    setProvidersFieldError(undefined)
    setSelectedProviderCodes([])
  }

  async function onSubmit(e: React.FormEvent){
    e.preventDefault()
    setErrorMessage(null)
    if(!form.name || !form.name.trim()){
      setFieldError({ name: 'Name is required' })
      return
    }

    if(!selectedProviderCodes || selectedProviderCodes.length === 0){
      setProvidersFieldError('Select at least one provider')
      return
    }

    setSaving(true)
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
      window.alert('Company saved')
      navigate('/companies')
    }catch(err:any){
      const axiosErr = err as any
      const detail =
        axiosErr?.response?.data?.detail ||
        axiosErr?.response?.statusText ||
        axiosErr?.message ||
        'Failed to save company'
      setErrorMessage(detail)
    }finally{
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto py-6">
        <div className="bg-white p-6 rounded shadow">
          <h1 className="text-2xl font-bold mb-4">{isEdit ? 'Edit Company' : 'Create Company'}</h1>

          {(countriesLoading || companyLoading) && (
            <div className="mb-4 text-sm text-gray-600">Loading...</div>
          )}

          {errorMessage && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-100 rounded">{errorMessage}</div>
          )}

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium">Name</label>
              <input name="name" value={form.name} onChange={onChange} className="mt-1 block w-full border rounded p-2" />
              {fieldError.name && <div className="text-red-600 text-sm mt-1">{fieldError.name}</div>}
            </div>

            <div>
              <label className="block text-sm font-medium">Country</label>
              <select name="country_code" value={form.country_code} onChange={onChange} className="mt-1 block w-full border rounded p-2" disabled={countriesLoading}>
                <option value="">Select country</option>
                {countries.map(c=> <option key={c.id} value={c.code}>{c.name}</option>)}
              </select>
            </div>

              <div>
                <label className="block text-sm font-medium">Supported Payment Providers</label>
                <div className="mt-2 mb-2 flex gap-2">
                  <button type="button" onClick={selectAllProviders} className="text-sm text-blue-600">Select all</button>
                  <button type="button" onClick={clearAllProviders} className="text-sm text-gray-600">Clear all</button>
                </div>
                {providersLoading ? (
                  <div className="text-sm text-gray-600">Loading providers...</div>
                ) : (
                  <div className="grid grid-cols-1 gap-2">
                    {providers.map(p => (
                      <label key={p.id} className="inline-flex items-center gap-2">
                        <input type="checkbox" checked={selectedProviderCodes.includes(p.code)} onChange={()=> toggleProvider(p.code)} />
                        <span className="text-sm">{p.name} ({p.code})</span>
                      </label>
                    ))}
                  </div>
                )}
                {providersFieldError && <div className="text-red-600 text-sm mt-1">{providersFieldError}</div>}
                {!providersLoading && providers.length === 0 && <div className="text-sm text-gray-600 mt-1">No payment providers available.</div>}
              </div>

            <div>
              <label className="block text-sm font-medium">Telegram Default Group ID</label>
              <input name="telegram_default_group_id" value={form.telegram_default_group_id} onChange={onChange} className="mt-1 block w-full border rounded p-2" />
            </div>

            <div className="flex items-center gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={saving || countriesLoading || companyLoading}>
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button type="button" onClick={()=> navigate('/companies')} className="px-4 py-2 border rounded bg-gray-50">Cancel</button>
            </div>
          </form>

          {company && (
            <div className="bg-gray-50 p-4 rounded mt-6">
              <h2 className="font-semibold">Result</h2>
              <div className="mt-2">API key: <code className="bg-white px-2 py-1 rounded">{company.api_key ?? '—'}</code></div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}
