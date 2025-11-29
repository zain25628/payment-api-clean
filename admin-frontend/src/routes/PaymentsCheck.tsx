import React, { useState } from 'react'

export const PaymentsCheck: React.FC = () => {
  const [amount, setAmount] = useState<number>(10)
  const [txnId, setTxnId] = useState<string>('')
  const [payerPhone, setPayerPhone] = useState<string>('')
  const [isChecking, setIsChecking] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<any | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setIsChecking(true)
    setLastResult(null)

    try {
      const payload: any = { order_id: `admin-check-${Date.now()}`, expected_amount: amount }
      if (txnId) payload.txn_id = txnId
      if (payerPhone) payload.payer_phone = payerPhone

      const res = await fetch('http://localhost:8000/payments/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Note: the backend resolves company via X-API-Key header. In admin UI
          // this request is unauthenticated; for local testing you may need to set
          // the appropriate header or use the browser extension to add `X-API-Key`.
        },
        body: JSON.stringify(payload),
      })

      const data = await res.json()
      setLastResult(data)
      if (!res.ok) {
        setError(`Status ${res.status}: ${JSON.stringify(data)}`)
      }
    } catch (err: any) {
      setError(err?.message || String(err))
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <h1 className="text-2xl font-semibold mb-4">Payments - Check</h1>

      <div className="bg-white shadow rounded p-4 mb-4">
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3">
          <div>
            <label className="block text-sm font-medium">Amount</label>
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
          <div>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={isChecking}>{isChecking? 'Checking...' : 'Check payment'}</button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      )}

      {lastResult && (
        <div className="bg-gray-50 rounded p-4">
          <h2 className="text-lg font-medium mb-2">Result</h2>
          <pre className="text-sm overflow-auto">{JSON.stringify(lastResult, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default PaymentsCheck
