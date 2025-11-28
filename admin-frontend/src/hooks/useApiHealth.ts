import { useCallback, useEffect, useState } from 'react'
import { checkHealth } from '../lib/api'

type Status = 'idle' | 'loading' | 'ok' | 'error'

export function useApiHealth() {
  const [status, setStatus] = useState<Status>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const run = useCallback(async () => {
    setStatus('loading')
    try {
      const res = await checkHealth()
      if (res && res.ok) {
        setStatus('ok')
        setErrorMessage(null)
      } else {
        console.error('Health check returned not ok', res)
        setStatus('error')
        setErrorMessage('Backend health check failed')
      }
    } catch (err) {
      console.error('Health check failed', err)
      setStatus('error')
      setErrorMessage('Backend health check failed')
    }
  }, [])

  useEffect(() => {
    run()
  }, [run])

  return { status, errorMessage, reload: run }
}

export default useApiHealth
