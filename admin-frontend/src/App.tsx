import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import CompaniesList from './routes/CompaniesList'
import CompanyForm from './routes/CompanyForm'
import CountriesList from './routes/CountriesList'
import PaymentProvidersList from './routes/PaymentProvidersList'
import CompanyWallets from './routes/CompanyWallets'
import { PaymentsCheck } from './routes/PaymentsCheck'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/companies" replace />} />
        <Route path="/companies" element={<CompaniesList />} />
        <Route path="/companies/new" element={<CompanyForm />} />
        <Route path="/companies/:id" element={<CompanyForm />} />
        <Route path="/companies/:id/wallets" element={<CompanyWallets />} />
        <Route path="/countries" element={<CountriesList />} />
        <Route path="/payment-providers" element={<PaymentProvidersList />} />
        <Route path="/payments/check" element={<PaymentsCheck />} />
      </Routes>
    </Layout>
  )
}
