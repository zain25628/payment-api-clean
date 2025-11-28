import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { fetchPaymentProviders, createPaymentProvider, fetchCountries } from '../lib/api'
import { AdminPaymentProvider, AdminCountry } from '../lib/types'

export default function PaymentProvidersList(){
  const [providers, setProviders] = useState<AdminPaymentProvider[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [countries, setCountries] = useState<AdminCountry[]>([])
  const [selectedCountryCode, setSelectedCountryCode] = useState<string | undefined>(undefined)
  const [saving, setSaving] = useState(false)

  useEffect(()=>{
    load()
    loadCountries()
  },[])

  async function loadCountries(){
    try{
      const cs = await fetchCountries()
      setCountries(cs)
    }catch(err:any){
      // silent for now; providers view can still work without country list
      console.warn('Failed to load countries for provider form', err)
    }
  }

  async function load(){
    setLoading(true)
    try{
      const data = await fetchPaymentProviders()
      setProviders(data)
      setError(null)
    }catch(err:any){
      setError(err?.message || 'Failed to load providers')
    }finally{
      setLoading(false)
    }
  }

  async function onSubmit(e: React.FormEvent){
    e.preventDefault()
    setError(null)
    if(!code.trim() || !name.trim()){
      setError('Code and name are required')
      return
    }
    setSaving(true)
    try{
      await createPaymentProvider({
        code: code.trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        country_code: selectedCountryCode || undefined,
      })
      setCode('')
      setName('')
      setDescription('')
      await load()
      window.alert('Provider created')
    }catch(err:any){
      const detail = err?.response?.data?.detail || err?.message || 'Create provider failed'
      setError(detail)
    }finally{
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto py-6">
        <div className="bg-white p-6 rounded shadow space-y-4">
          <h1 className="text-2xl font-bold">Payment Providers</h1>
          {error && <div className="p-2 bg-red-50 text-red-700 rounded">{error}</div>}

          <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3">
            <div>
              <label className="block text-sm font-medium">Code</label>
              <input value={code} onChange={e=>setCode(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Country (optional)</label>
              <select value={selectedCountryCode ?? ''} onChange={e=> setSelectedCountryCode(e.target.value || undefined)} className="mt-1 block w-full border rounded p-2">
                <option value="">(none)</option>
                {countries.map(c => <option key={c.id} value={c.code}>{c.name} ({c.code})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium">Name</label>
              <input value={name} onChange={e=>setName(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Description (optional)</label>
              <input value={description} onChange={e=>setDescription(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={saving}>{saving? 'Saving...' : 'Save'}</button>
            </div>
          </form>

          <div>
            {loading ? (
              <div>Loading...</div>
            ) : providers.length === 0 ? (
              <div>No providers yet.</div>
            ) : (
              <div className="overflow-x-auto bg-white rounded shadow">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-2">ID</th>
                      <th className="p-2">Code</th>
                      <th className="p-2">Name</th>
                      <th className="p-2">Description</th>
                      <th className="p-2">Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providers.map(p => (
                      <tr key={p.id} className="border-t">
                        <td className="p-2 align-top">{p.id}</td>
                        <td className="p-2 align-top">{p.code}</td>
                        <td className="p-2 align-top">{p.name}</td>
                        <td className="p-2 align-top">{p.description ?? '—'}</td>
                        <td className="p-2 align-top">{p.country_code ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
