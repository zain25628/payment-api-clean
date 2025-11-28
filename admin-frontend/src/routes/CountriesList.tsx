import React, { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { fetchCountries, createCountry } from '../lib/api'
import { AdminCountry } from '../lib/types'

export default function CountriesList(){
  const [countries, setCountries] = useState<AdminCountry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(()=>{
    let mounted = true
    setLoading(true)
    fetchCountries()
      .then(data => { if(mounted) setCountries(data) })
      .catch(()=> { if(mounted) setError('Failed to load countries') })
      .finally(()=> mounted && setLoading(false))

    return ()=> { mounted = false }
  },[])

  async function loadCountries(){
    setLoading(true)
    try{
      const data = await fetchCountries()
      setCountries(data)
      setError(null)
    }catch(err:any){
      setError(err?.message || 'Failed to load countries')
    }finally{
      setLoading(false)
    }
  }

  async function onSubmit(e: React.FormEvent){
    e.preventDefault()
    setError(null)
    if(!code || !code.trim() || !name || !name.trim()){
      setError('Both code and name are required')
      return
    }
    setSaving(true)
    try{
      await createCountry({ code: code.trim(), name: name.trim() })
      setCode('')
      setName('')
      await loadCountries()
      window.alert('Country created')
    }catch(err:any){
      console.error('createCountry failed', err)
      window.alert('Failed to create country')
      setError(err?.message || 'Create country failed')
    }finally{
      setSaving(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-3xl mx-auto py-6">
        <div className="bg-white p-6 rounded shadow space-y-4">
          <h1 className="text-2xl font-bold">Countries</h1>

          {error && <div className="p-2 bg-red-50 text-red-700 rounded">{error}</div>}

          <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3">
            <div>
              <label className="block text-sm font-medium">Code</label>
              <input value={code} onChange={e=>setCode(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Name</label>
              <input value={name} onChange={e=>setName(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={saving}>{saving ? 'Saving...' : 'Save'}</button>
            </div>
          </form>

          <div>
            {loading ? (
              <div>Loading...</div>
            ) : countries.length === 0 ? (
              <div>No countries yet.</div>
            ) : (
              <div className="overflow-x-auto bg-white rounded shadow">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-2">ID</th>
                      <th className="p-2">Code</th>
                      <th className="p-2">Name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {countries.map(c => (
                      <tr key={c.id} className="border-t">
                        <td className="p-2 align-top">{c.id}</td>
                        <td className="p-2 align-top">{c.code}</td>
                        <td className="p-2 align-top">{c.name}</td>
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
