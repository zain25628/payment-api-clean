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
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    code?: string;
    country_code?: string;
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(()=>{
    load()
    loadCountries()
  },[])

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <h1 className="text-2xl font-bold">Payment Providers</h1>
          <p className="text-sm text-gray-600">Create and manage payment providers used by channels and wallets.</p>

          {error && <div className="p-2 bg-red-50 text-red-700 rounded">{error}</div>}

          <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {formError && (
              <div className="md:col-span-2 mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
            )}
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
              {fieldErrors.country_code && (<p className="mt-1 text-sm text-red-500">{fieldErrors.country_code}</p>)}
            </div>
            <div>
              <label className="block text-sm font-medium">Name</label>
              <input value={name} onChange={e=>setName(e.target.value)} className="mt-1 block w-full border rounded p-2" />
              {fieldErrors.name && (<p className="mt-1 text-sm text-red-500">{fieldErrors.name}</p>)}
            </div>
            <div>
              <label className="block text-sm font-medium">Description (optional)</label>
              <input value={description} onChange={e=>setDescription(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div className="md:col-span-2 flex items-center">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50" disabled={isSubmitting || saving}>{isSubmitting || saving? 'Saving...' : 'Save'}</button>
            </div>
          </form>

          <div>
            {loading ? (
              <div>Loading...</div>
            ) : providers.length === 0 ? (
              <div>No providers yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-3">ID</th>
                      <th className="p-3">Code</th>
                      <th className="p-3">Name</th>
                      <th className="p-3">Description</th>
                      <th className="p-3">Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {providers.map(p => (
                      <tr key={p.id} className="border-t hover:bg-gray-50">
                        <td className="p-3 align-top text-right">{p.id}</td>
                        <td className="p-3 align-top">{p.code}</td>
                        <td className="p-3 align-top">{p.name}</td>
                        <td className="p-3 align-top">{p.description ?? '—'}</td>
                        <td className="p-3 align-top">{p.country_code ?? '—'}</td>
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
