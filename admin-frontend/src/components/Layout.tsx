import React from 'react'
import { NavLink } from 'react-router-dom'
import useApiHealth from '../hooks/useApiHealth'

const NavItem: React.FC<{to:string, children: React.ReactNode}> = ({to, children}) => (
  <NavLink to={to} className={({isActive}) => `block px-3 py-2 rounded ${isActive? 'bg-gray-200' : 'hover:bg-gray-100'}`}>
    {children}
  </NavLink>
)

const Layout: React.FC<{children: React.ReactNode}> = ({children}) => {
  const { status, errorMessage, reload } = useApiHealth()
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="text-lg font-semibold">Payment Gateway Admin</div>
          <div className="text-sm text-gray-600">Developer UI</div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 md:grid-cols-6 gap-6">
        <aside className="md:col-span-1 bg-white border rounded-lg p-4 shadow-sm">
          <nav className="space-y-2">
            <NavItem to="/companies">Companies</NavItem>
            <NavItem to="/companies/new">Create Company</NavItem>
            <NavItem to="/companies/1/wallets">Company Wallets</NavItem>
            <NavItem to="/payment-providers">Payment Providers</NavItem>
              <NavItem to="/payments/history">Payments history</NavItem>
            <NavItem to="/payments/check">Payments (check & verify)</NavItem>
            <NavItem to="/countries">Countries</NavItem>
          </nav>
        </aside>

        <main className="md:col-span-5">
          <div className="flex items-center justify-end mb-4">
            {status === 'ok' && (
              <div className="px-2 py-1 bg-green-100 text-green-800 rounded">API: OK</div>
            )}
            {status === 'error' && (
              <div className="flex items-center gap-2">
                <div className="px-2 py-1 bg-red-100 text-red-800 rounded">API: DOWN</div>
                <button onClick={reload} className="px-2 py-1 bg-gray-100 rounded text-sm">Retry</button>
              </div>
            )}
            {(status === 'idle' || status === 'loading') && (
              <div className="px-2 py-1 bg-gray-100 text-gray-700 rounded">API: Checking...</div>
            )}
          </div>
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout
