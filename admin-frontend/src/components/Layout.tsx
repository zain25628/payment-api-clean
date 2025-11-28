import React from 'react'
import { NavLink } from 'react-router-dom'
import useApiHealth from '../hooks/useApiHealth'

const NavItem: React.FC<{to:string, children: React.ReactNode}> = ({to, children}) => (
  <NavLink to={to} className={({isActive}) => `px-3 py-2 rounded ${isActive? 'bg-gray-200' : 'hover:bg-gray-100'}`}>
    {children}
  </NavLink>
)

const Layout: React.FC<{children: React.ReactNode}> = ({children}) => {
  const { status, errorMessage, reload } = useApiHealth()
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-white border-r">
        <div className="p-4 font-bold">Admin Dashboard</div>
        <nav className="p-4 space-y-2">
          <NavItem to="/companies">Companies</NavItem>
          <NavItem to="/countries">Countries</NavItem>
          <NavItem to="/payment-providers">Payment Providers</NavItem>
          <NavItem to="/companies/new">Create Company</NavItem>
        </nav>
      </aside>
      <main className="flex-1 p-6">
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
  )
}

export default Layout
