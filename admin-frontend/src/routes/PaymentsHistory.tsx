import React, { useState } from 'react'
import Layout from '../components/Layout'

type MatchResponse = {
  found: boolean
  match: boolean
  payment_id?: number
  txn_id?: string
  status?: string
}

const DEFAULT_API_KEY = process.env.NODE_ENV === 'development' ? 'dev-channel-key' : ''

export default function PaymentsHistory(){
  const [apiKey, setApiKey] = useState<string>(DEFAULT_API_KEY)
  const [txnId, setTxnId] = useState<string>('')
  const [amount, setAmount] = useState<number | ''>('')
  const [minAmount, setMinAmount] = useState<number | ''>('')
  const [maxAmount, setMaxAmount] = useState<number | ''>('')
  const [status, setStatus] = useState<string>('any')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<MatchResponse | null>(null)

  // Note: backend currently exposes POST /payments/check and /payments/match
  // but does not provide a paginated admin listing endpoint. The best we
  // can do without backend changes is search for a single payment using
  // the match/check endpoints. To find a specific payment, provide a
  // txn_id and amount (amount is required by the match endpoint).

  async function onFilter(e: React.FormEvent){
    e.preventDefault()
    setError(null)
    setResult(null)

    if(!txnId){
      setError('Backend does not support listing — provide a Txn ID and amount to search for a payment.')
      return
    }
    if(amount === '' || Number(amount) <= 0){
      setError('Amount is required for the backend match endpoint.')
      return
    }

    setLoading(true)
    try{
      const payload = { txn_id: txnId.trim(), amount: Number(amount) }
      const res = await fetch('http://localhost:8000/payments/match', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.trim() }, body: JSON.stringify(payload)
      })
      const data = await res.json()
      if(!res.ok){
        setError(data?.detail || JSON.stringify(data))
      } else {
        setResult(data as MatchResponse)
      }
    }catch(err:any){
      setError(err?.message || String(err))
    }finally{ setLoading(false) }
  }

  function onReset(){
    setTxnId('')
    setAmount('')
    setMinAmount('')
    setMaxAmount('')
    setStatus('any')
    setError(null)
    setResult(null)
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-bold">Payments history</h1>
          <p className="text-sm text-gray-600 mb-4">Search payments. Note: backend currently supports single-item search via txn_id + amount; there is no paginated admin list endpoint.</p>

          <form onSubmit={onFilter} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div className="md:col-span-1">
              <label className="block text-sm font-medium">Txn ID</label>
              <input value={txnId} onChange={e=>setTxnId(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Amount</label>
              <input type="number" value={amount as any} onChange={e=>setAmount(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Min amount (not supported server-side)</label>
              <input type="number" value={minAmount as any} onChange={e=>setMinAmount(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Max amount (not supported server-side)</label>
              <input type="number" value={maxAmount as any} onChange={e=>setMaxAmount(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
            </div>

            <div className="md:col-span-1">
              <label className="block text-sm font-medium">Status</label>
              <select value={status} onChange={e=>setStatus(e.target.value)} className="mt-1 block w-full border rounded p-2">
                <option value="any">Any</option>
                <option value="new">New</option>
                <option value="used">Used</option>
              </select>
            </div>

            <div className="md:col-span-3 flex items-end gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={loading}>{loading ? 'Searching...' : 'Filter'}</button>
              <button type="button" onClick={onReset} className="px-3 py-2 border rounded bg-gray-50">Reset</button>
            </div>
          </form>

          {error && <div className="mb-4 p-2 bg-red-50 text-red-700 rounded">{error}</div>}

          <div>
            {loading ? (
              <div>Loading...</div>
            ) : !result ? (
              <div className="text-sm text-gray-600">No results. Use txn_id + amount to search for a payment.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-3">ID</th>
                      <th className="p-3">Txn ID</th>
                      <th className="p-3">Amount</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Created at</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.found ? (
                      <tr className="border-t hover:bg-gray-50">
                        <td className="p-3 align-top text-right">{result.payment_id ?? '—'}</td>
                        <td className="p-3 align-top">{result.txn_id ?? '—'}</td>
                        <td className="p-3 align-top text-right">{/* amount not returned by match response */ '—'}</td>
                        <td className="p-3 align-top">{result.status ?? (result.match ? 'match' : 'mismatch')}</td>
                        <td className="p-3 align-top">—</td>
                      </tr>
                    ) : (
                      <tr><td colSpan={5} className="p-4 text-center text-gray-600">No payment found.</td></tr>
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
