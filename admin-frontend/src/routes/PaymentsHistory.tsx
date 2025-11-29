import React, { useState } from 'react'
import Layout from '../components/Layout'
import { fetchAdminPayments } from '../lib/api'

type PaymentRow = {
  payment_id: number
  company_id: number
  company_name?: string
  channel_id?: number
  channel_name?: string
  wallet_id?: number
  txn_id?: string
  amount: number
  currency: string
  status: string
  payer_phone?: string
  created_at: string
  used_at?: string
}

export default function PaymentsHistory(){
  const [txnId, setTxnId] = useState<string>('')
  const [minAmount, setMinAmount] = useState<number | ''>('')
  const [maxAmount, setMaxAmount] = useState<number | ''>('')
  const [status, setStatus] = useState<string>('any')
  const [createdFrom, setCreatedFrom] = useState<string>('')
  const [createdTo, setCreatedTo] = useState<string>('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<PaymentRow[]>([])
  const [total, setTotal] = useState<number>(0)
  const [page, setPage] = useState<number>(1)
  const [pageSize] = useState<number>(25)

  async function load(pageToLoad = 1){
    setLoading(true)
    setError(null)
    try{
      const params:any = { page: pageToLoad, page_size: pageSize }
      if(txnId) params.txn_id = txnId
      if(minAmount !== '') params.min_amount = Number(minAmount)
      if(maxAmount !== '') params.max_amount = Number(maxAmount)
      if(status && status !== 'any') params.status = status
      if(createdFrom) params.created_from = new Date(createdFrom).toISOString()
      if(createdTo) params.created_to = new Date(createdTo).toISOString()

      const resp = await fetchAdminPayments(params)
      setItems(resp.items || [])
      setTotal(resp.total || 0)
      setPage(resp.page || pageToLoad)
    }catch(err:any){
      setError(err?.message || String(err))
    }finally{ setLoading(false) }
  }

  function onReset(){
    setTxnId('')
    setMinAmount('')
    setMaxAmount('')
    setStatus('any')
    setCreatedFrom('')
    setCreatedTo('')
    setItems([])
    setTotal(0)
    setPage(1)
    setError(null)
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow p-6">
          <h1 className="text-2xl font-bold">Payments history</h1>
          <p className="text-sm text-gray-600 mb-4">Search and review payments by amount, status, date, or transaction ID.</p>

          <form onSubmit={(e)=>{ e.preventDefault(); load(1) }} className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium">Txn ID</label>
              <input value={txnId} onChange={e=>setTxnId(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Min amount</label>
              <input type="number" value={minAmount as any} onChange={e=>setMinAmount(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Max amount</label>
              <input type="number" value={maxAmount as any} onChange={e=>setMaxAmount(e.target.value === '' ? '' : Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Status</label>
              <select value={status} onChange={e=>setStatus(e.target.value)} className="mt-1 block w-full border rounded p-2">
                <option value="any">Any</option>
                <option value="new">New</option>
                <option value="pending_confirmation">Pending</option>
                <option value="used">Used</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium">Created from</label>
              <input type="date" value={createdFrom} onChange={e=>setCreatedFrom(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium">Created to</label>
              <input type="date" value={createdTo} onChange={e=>setCreatedTo(e.target.value)} className="mt-1 block w-full border rounded p-2" />
            </div>

            <div className="md:col-span-2 flex items-end gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={loading}>{loading ? 'Filtering...' : 'Filter'}</button>
              <button type="button" onClick={onReset} className="px-3 py-2 border rounded bg-gray-50">Reset</button>
            </div>
          </form>

          {error && <div className="mb-4 p-2 bg-red-50 text-red-700 rounded">{error}</div>}

          <div>
            {loading ? (
              <div>Loading...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr className="text-left">
                      <th className="p-3">ID</th>
                      <th className="p-3">Company</th>
                      <th className="p-3">Channel</th>
                      <th className="p-3">Txn ID</th>
                      <th className="p-3 text-right">Amount</th>
                      <th className="p-3">Currency</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Created at</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.length === 0 ? (
                      <tr><td colSpan={8} className="p-4 text-center text-gray-600">No payments found.</td></tr>
                    ) : (
                      items.map(p => (
                        <tr key={p.payment_id} className="border-t hover:bg-gray-50">
                          <td className="p-3 align-top text-right">{p.payment_id}</td>
                          <td className="p-3 align-top">{p.company_name ?? p.company_id}</td>
                          <td className="p-3 align-top">{p.channel_name ?? p.channel_id ?? '—'}</td>
                          <td className="p-3 align-top">{p.txn_id ?? '—'}</td>
                          <td className="p-3 align-top text-right">{p.amount.toLocaleString()}</td>
                          <td className="p-3 align-top">{p.currency}</td>
                          <td className="p-3 align-top">{p.status}</td>
                          <td className="p-3 align-top">{new Date(p.created_at).toLocaleString()}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>

                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-600">Total: {total}</div>
                  <div className="flex items-center gap-2">
                    <button className="px-3 py-1 border rounded" disabled={page <= 1} onClick={()=> load(page-1)}>Previous</button>
                    <div className="text-sm">Page {page} / {totalPages}</div>
                    <button className="px-3 py-1 border rounded" disabled={page >= totalPages} onClick={()=> load(page+1)}>Next</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}
