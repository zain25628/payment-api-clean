import React, { useState } from 'react'

type PaymentSummary = {
  payment_id: number
  txn_id?: string
  amount: number
  currency?: string
  created_at?: string
}

type PaymentsCheckResult = {
  found: boolean
  match: boolean
  reason?: string
  confirm_token?: string
  order_id?: string
  payment?: PaymentSummary | null
}

const DEFAULT_API_KEY = process.env.NODE_ENV === 'development' ? 'dev-channel-key' : ''

export const PaymentsCheck: React.FC = () => {
  const [apiKey, setApiKey] = useState<string>(DEFAULT_API_KEY)
  const [orderId, setOrderId] = useState<string>(`admin-check-${Date.now()}`)
  const [amount, setAmount] = useState<number>(10)
  const [txnId, setTxnId] = useState<string>('')
  const [payerPhone, setPayerPhone] = useState<string>('')
  const [isChecking, setIsChecking] = useState<boolean>(false)
  const [isConfirming, setIsConfirming] = useState<boolean>(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)
  const [result, setResult] = useState<PaymentsCheckResult | null>(null)

  function formatCurrency(n?: number) {
    if (n == null || Number.isNaN(Number(n))) return '—'
    return Number(n).toLocaleString()
  }

  function formatDate(s?: string) {
    if (!s) return '—'
    try { return new Date(s).toLocaleString() } catch { return s }
  }

  async function onCheck(e: React.FormEvent) {
    e.preventDefault()
    setFormError(null)
    setServerError(null)
    setResult(null)

    if (!apiKey || !apiKey.trim()) { setFormError('API key is required'); return }
    if (!orderId || !orderId.trim()) { setFormError('Order ID is required'); return }
    if (!amount || Number(amount) <= 0) { setFormError('Expected amount must be greater than 0'); return }

    setIsChecking(true)
    try {
      const payload: any = { order_id: orderId.trim(), expected_amount: Number(amount) }
      if (txnId) payload.txn_id = txnId
      if (payerPhone) payload.payer_phone = payerPhone

      const res = await fetch('http://localhost:8000/payments/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.trim() },
        body: JSON.stringify(payload),
      })

      const data = await res.json()
      if (!res.ok) {
        setServerError(data?.detail || JSON.stringify(data))
        setResult(data as PaymentsCheckResult)
      } else {
        setResult(data as PaymentsCheckResult)
      }
    } catch (err: any) {
      setServerError(err?.message || String(err))
    } finally {
      setIsChecking(false)
    }
  }

  async function onConfirm() {
    if (!result || !result.payment || !result.confirm_token) return
    setIsConfirming(true)
    setServerError(null)
    try {
      const body = { payment_id: result.payment.payment_id, confirm_token: result.confirm_token }
      const res = await fetch('http://localhost:8000/payments/confirm', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.trim() }, body: JSON.stringify(body)
      })
      const data = await res.json()
      if (!res.ok) {
        setServerError(data?.detail || JSON.stringify(data))
      } else {
        // success — show response and refresh check for same order
        setServerError(null)
        // refetch the same check to get updated state
        await (async () => {
          const payload = { order_id: orderId.trim(), expected_amount: Number(amount) }
          if (txnId) (payload as any).txn_id = txnId
          if (payerPhone) (payload as any).payer_phone = payerPhone
          const r = await fetch('http://localhost:8000/payments/check', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey.trim() }, body: JSON.stringify(payload) })
          const d = await r.json()
          setResult(d as PaymentsCheckResult)
        })()
      }
    } catch (err: any) {
      setServerError(err?.message || String(err))
    } finally {
      setIsConfirming(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-1">Payments — Check & Confirm</h1>
      <p className="text-sm text-gray-600 mb-4">Use this tool to find incoming payments and mark them as used.</p>

      <div className="bg-white shadow rounded p-4 mb-4">
        <form onSubmit={onCheck} className="grid grid-cols-1 gap-3">
          {formError && <div className="text-sm text-red-700 bg-red-50 border border-red-100 px-3 py-2 rounded">{formError}</div>}
          <div>
            <label className="block text-sm font-medium">API key (X-API-Key)</label>
            <input type="text" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="dev-channel-key" className="mt-1 block w-full border rounded p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium">Order ID</label>
            <input value={orderId} onChange={e=>setOrderId(e.target.value)} className="mt-1 block w-full border rounded p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium">Expected amount</label>
            <input type="number" value={amount} onChange={e=>setAmount(Number(e.target.value))} className="mt-1 block w-full border rounded p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium">Txn ID (optional)</label>
            <input value={txnId} onChange={e=>setTxnId(e.target.value)} className="mt-1 block w-full border rounded p-2" />
          </div>
          <div>
            <label className="block text-sm font-medium">Payer Phone (optional)</label>
            <input value={payerPhone} onChange={e=>setPayerPhone(e.target.value)} className="mt-1 block w-full border rounded p-2" />
          </div>

          <div className="flex items-center gap-3">
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50" disabled={isChecking}>{isChecking? 'Checking...' : 'Check payment'}</button>
            <button type="button" onClick={() => { setOrderId(`admin-check-${Date.now()}`); setTxnId(''); setPayerPhone(''); setResult(null); setFormError(null); setServerError(null); }} className="px-3 py-2 border rounded bg-gray-50">Reset</button>
          </div>
        </form>
      </div>

      {serverError && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{serverError}</div>
      )}

      {result && (
        <div className="bg-gray-50 rounded p-4">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-medium">Result</h2>
              <div className="mt-2">
                <span className={`inline-block px-2 py-1 rounded text-sm ${result.found ? (result.match ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800') : 'bg-gray-100 text-gray-800'}`}>
                  {result.found ? (result.match ? 'Match' : 'Mismatch') : 'Not found'}
                </span>
                {result.reason && <div className="text-sm text-gray-600 mt-1">{result.reason}</div>}
              </div>
            </div>
            <div className="text-right">
              {result.confirm_token && <div className="text-sm text-gray-600">Confirm token available</div>}
            </div>
          </div>

          {result.payment && (
            <div className="mt-4 bg-white p-3 rounded border">
              <div className="text-sm text-gray-600">Payment</div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                <div><strong>ID:</strong> {result.payment.payment_id}</div>
                <div><strong>Txn:</strong> {result.payment.txn_id ?? '—'}</div>
                <div><strong>Amount:</strong> {formatCurrency(result.payment.amount)}</div>
                <div><strong>Currency:</strong> {result.payment.currency ?? '—'}</div>
                <div><strong>Created:</strong> {formatDate(result.payment.created_at)}</div>
              </div>
            </div>
          )}

          {result.confirm_token && (
            <div className="mt-4">
              <label className="block text-sm font-medium">Confirm token</label>
              <div className="mt-1 flex gap-2">
                <input readOnly value={result.confirm_token} className="flex-1 p-2 border rounded bg-white" />
                <button className="px-3 py-2 border rounded" onClick={() => navigator.clipboard?.writeText(result.confirm_token || '')}>Copy</button>
              </div>
            </div>
          )}

          <div className="mt-4 flex items-center gap-2">
            <button disabled={!(result.found && result.match && result.payment && result.confirm_token) || isConfirming} onClick={onConfirm} className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50">{isConfirming? 'Confirming...' : 'Confirm usage'}</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default PaymentsCheck
