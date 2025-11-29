import React, {useEffect, useMemo, useState} from 'react'
import { fetchCompanies, toggleCompany } from '../lib/api'
import { AdminCompanyListItem } from '../lib/types'
import Layout from '../components/Layout'
import { Link, useNavigate } from 'react-router-dom'

function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString()
}

export default function CompaniesList(){
  const [companies, setCompanies] = useState<AdminCompanyListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(()=>{
    let mounted = true
    setLoading(true)
    fetchCompanies().then(data=>{
      if(mounted){ setCompanies(data) }
    }).catch(err=>{
      setError(err?.message || 'Failed to load')
    }).finally(()=> mounted && setLoading(false))

    return ()=>{ mounted = false }
  },[])

  async function handleToggle(id:number){
    try{
      const updated = await toggleCompany(id)
      setCompanies(cs => cs.map(c => c.id === updated.id ? {...c, is_active: updated.is_active} : c))
    }catch(err){
      console.error(err)
      setError('Toggle failed')
    }
  }

  function partialKey(key?: string){
    if(!key) return '—'
    if(key.length <= 8) return key
    return `${key.slice(0,4)}***${key.slice(-4)}`
  }

  async function copyKey(key?: string){
    if(!key) return
    try{
      if(navigator && navigator.clipboard && navigator.clipboard.writeText){
        await navigator.clipboard.writeText(key)
        window.alert('Copied')
      } else {
        // fallback
        const ta = document.createElement('textarea')
        ta.value = key
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
        window.alert('Copied')
      }
    }catch(err){
      console.error('copy failed', err)
      window.alert('Copy failed')
    }
  }

  const filtered = useMemo(()=>{
    const q = search.trim().toLowerCase()
    if(!q) return companies
    return companies.filter(c => {
      const name = (c.name || '').toLowerCase()
      const country = (c.country_code || '').toLowerCase()
      const key = (c.api_key || '').toLowerCase()
      return name.includes(q) || country.includes(q) || key.includes(q)
    })
  },[companies, search])

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold">الشركات (Companies)</h1>
            <p className="text-sm text-gray-600">Manage companies, API keys and basic settings.</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              value={search}
              onChange={e=>setSearch(e.target.value)}
              placeholder="Search by name, country, or API key..."
              className="border rounded p-2"
            />
            <Link to="/companies/new" className="px-4 py-2 bg-blue-600 text-white rounded">Create Company</Link>
          </div>
        </div>

        {loading && <div>Loading...</div>}
        {error && <div className="text-red-600">{error}</div>}

        <div className="bg-white rounded-xl shadow p-6">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left">
                <th className="p-3">ID</th>
                <th className="p-3">Name</th>
                <th className="p-3">Country</th>
                <th className="p-3">Active</th>
                <th className="p-3">API Key</th>
                <th className="p-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 align-top text-right">{formatNumber(c.id)}</td>
                  <td className="p-3 align-top">{c.name}</td>
                  <td className="p-3 align-top">{c.country_code ?? 'N/A'}</td>
                  <td className="p-3 align-top">
                    <span className={`px-2 py-1 rounded text-sm ${c.is_active? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{c.is_active? 'Active':'Disabled'}</span>
                  </td>
                  <td className="p-3 align-top">
                    <code className="bg-gray-100 px-2 py-1 rounded mr-2">{partialKey(c.api_key)}</code>
                    <button onClick={()=>copyKey(c.api_key)} className="px-2 py-1 border rounded">Copy</button>
                  </td>
                  <td className="p-3 align-top flex gap-2">
                    <Link to={`/companies/${c.id}/wallets`} className="px-3 py-1 bg-gray-100 text-blue-600 rounded">Wallets</Link>
                    <Link to={`/companies/${c.id}`} className="px-3 py-1 bg-gray-200 rounded">Details</Link>
                    <button onClick={()=>handleToggle(c.id)} className="px-3 py-1 bg-gray-200 rounded">Toggle</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  )
}
