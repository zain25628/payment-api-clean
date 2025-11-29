import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { fetchCompanyWallets, toggleWallet, createCompanyWallet, getCompany } from '../lib/api'
import { AdminWalletOut, AdminChannelOut } from '../lib/types'

function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString()
}

export default function CompanyWallets(){
  const { id } = useParams<{id: string}>()
  const navigate = useNavigate()
  const companyId = Number(id)

  // If the companyId is invalid, show a simple message and a back button
  if (Number.isNaN(companyId) || companyId <= 0) {
    return (
      <Layout>
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold">Company Wallets</h1>
            <div>
              <button onClick={()=> navigate('/companies')} className="px-3 py-1 bg-gray-200 rounded">Back to Companies</button>
            </div>
          </div>
          <div className="p-4 bg-yellow-50 text-yellow-800 rounded">Invalid company id</div>
        </div>
      </Layout>
    )
  }

  const [wallets, setWallets] = useState<AdminWalletOut[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [walletLabel, setWalletLabel] = useState<string>('')
  const [walletIdentifier, setWalletIdentifier] = useState<string>('')
  const [dailyLimit, setDailyLimit] = useState<number>(0)
  const [channelId, setChannelId] = useState<number | ''>('')
  const [isActive, setIsActive] = useState<boolean>(true)
  const [fieldErrors, setFieldErrors] = useState<{
    wallet_label?: string;
    wallet_identifier?: string;
    daily_limit?: string;
    channel_id?: string;
  }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [channels, setChannels] = useState<AdminChannelOut[]>([])

  useEffect(()=>{
    let mounted = true
    setLoading(true)
    fetchCompanyWallets(companyId)
      .then(ws => { if(mounted) { setWallets(ws); setError(null) } })
      .catch(err => { console.error('fetchCompanyWallets failed', err); if(mounted) setError('Failed to load wallets') })
      .finally(()=> mounted && setLoading(false))

    // fetch company details to get channels for the create form
    getCompany(companyId)
      .then(c => {
        if(!mounted) return
        const chs = (c && (c.channels || c.channels === null) ? c.channels : c.channels) as any
        if(!chs || chs.length === 0) {
          console.log('Company has no channels')
          setChannels([])
        } else {
          setChannels(chs)
        }
      })
      .catch(err => {
        console.error('getCompany failed', err)
        setChannels([])
      })

    return ()=>{ mounted = false }
  }, [companyId])

  async function handleToggle(walletId: number){
    try{
      const updated = await toggleWallet(walletId)
      setWallets(ws => ws.map(w => w.id === updated.id ? updated : w))
    }catch(err){
      console.error('toggleWallet failed', err)
      alert('Failed to toggle wallet')
      setError('Failed to toggle wallet')
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setFormError(null)

    const errors: typeof fieldErrors = {}
    if (!walletLabel || !walletLabel.trim()) errors.wallet_label = 'Wallet label is required'
    if (!walletIdentifier || !walletIdentifier.trim()) errors.wallet_identifier = 'Wallet identifier is required'
    if (!dailyLimit || Number(dailyLimit) <= 0) errors.daily_limit = 'Daily limit must be greater than 0'
    if (channelId === '' || channelId === null) errors.channel_id = 'Channel is required'

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      setFormError(null)
      return
    }

    setFieldErrors({})
    setFormError(null)
    setIsSubmitting(true)

    const payload = {
      wallet_label: walletLabel,
      wallet_identifier: walletIdentifier,
      daily_limit: Number(dailyLimit),
      is_active: Boolean(isActive),
      channel_id: Number(channelId),
    }

    try {
      const created = await createCompanyWallet(companyId, payload)
      setWallets(ws => [...ws, created])
      // clear form
      setWalletLabel('')
      setWalletIdentifier('')
      setDailyLimit(0)
      setChannelId('')
      setIsActive(true)
    } catch (err: any) {
      console.error('createCompanyWallet failed', err)
      const detail = err?.response?.data?.detail
      setFormError(typeof detail === 'string' ? detail : (err?.message ?? 'Failed to create wallet'))
      setError(typeof detail === 'string' ? detail : 'Failed to create wallet')
      alert(typeof detail === 'string' ? detail : 'Failed to create wallet')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold">Company Wallets</h1>
            <p className="text-sm text-gray-600">Create and manage company wallets and view daily usage.</p>
          </div>
          <div>
            <button onClick={()=> navigate('/companies')} className="px-3 py-1 bg-gray-200 rounded">Back to Companies</button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-medium mb-3">Create Wallet</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              {formError && (
                <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</div>
              )}
              <div>
                <label className="block text-sm font-medium">Wallet Label</label>
                <input placeholder="Wallet Label" value={walletLabel} onChange={e => setWalletLabel(e.target.value)} className="mt-1 p-2 border rounded w-full" />
                {fieldErrors.wallet_label && <p className="mt-1 text-sm text-red-500">{fieldErrors.wallet_label}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium">Wallet Identifier</label>
                <input placeholder="Wallet Identifier" value={walletIdentifier} onChange={e => setWalletIdentifier(e.target.value)} className="mt-1 p-2 border rounded w-full" />
                {fieldErrors.wallet_identifier && <p className="mt-1 text-sm text-red-500">{fieldErrors.wallet_identifier}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium">Daily Limit</label>
                <input type="number" placeholder="Daily Limit" value={dailyLimit} onChange={e => setDailyLimit(Number(e.target.value))} className="mt-1 p-2 border rounded w-full" />
                {fieldErrors.daily_limit && <p className="mt-1 text-sm text-red-500">{fieldErrors.daily_limit}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium">Channel</label>
                <select value={channelId as any} onChange={e => setChannelId(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 p-2 border rounded w-full">
                  <option value="">Select channel...</option>
                  {channels.map(ch => (
                    <option key={ch.id} value={ch.id}>{ch.provider_name ?? ch.provider_code ?? `Channel ${ch.id}`}</option>
                  ))}
                </select>
                {fieldErrors.channel_id && <p className="mt-1 text-sm text-red-500">{fieldErrors.channel_id}</p>}
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2"><input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} /> Active</label>
                <button type="submit" disabled={isSubmitting} className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50">{isSubmitting ? 'Creating...' : 'Create Wallet'}</button>
              </div>
            </form>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-medium mb-3">Wallets</h2>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-700 rounded">{error}</div>}
            {loading ? (
              <div>Loading...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-3">Label</th>
                      <th className="p-3">Identifier</th>
                      <th className="p-3 text-right">Daily limit</th>
                      <th className="p-3 text-right">Used today</th>
                      <th className="p-3">Provider</th>
                      <th className="p-3">Active</th>
                      <th className="p-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wallets.map(w => (
                      <tr key={w.id} className="border-t hover:bg-gray-50">
                        <td className="p-3 align-top">{w.wallet_label}</td>
                        <td className="p-3 align-top">{w.wallet_identifier}</td>
                        <td className="p-3 align-top text-right">{formatNumber(w.daily_limit)}</td>
                        <td className="p-3 align-top text-right">{formatNumber(w.used_today ?? 0)}</td>
                        <td className="p-3 align-top">{w.provider_name ?? w.provider_code ?? '—'}</td>
                        <td className="p-3 align-top">{w.is_active ? 'Yes' : 'No'}</td>
                        <td className="p-3 align-top">
                          <button onClick={()=> handleToggle(w.id)} className="px-3 py-1 bg-gray-200 rounded">Toggle Active</button>
                        </td>
                      </tr>
                    ))}
                    {wallets.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-4 text-center text-gray-600">No wallets found.</td>
                      </tr>
                    )}
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
