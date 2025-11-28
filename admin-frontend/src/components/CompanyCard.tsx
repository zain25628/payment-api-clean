import React from 'react'
import { AdminCompanyListItem } from '../lib/types'

type Props = {
  company: AdminCompanyListItem
  onToggle: (id:number)=>void
  onOpen: (id:number)=>void
}

const CompanyCard: React.FC<Props> = ({company, onToggle, onOpen}) => {
  return (
    <div className="bg-white shadow-sm rounded p-4 flex items-center justify-between">
      <div>
        <div className="text-lg font-semibold">{company.name}</div>
        <div className="text-sm text-gray-600">{company.country_code ?? '—'}</div>
      </div>
      <div className="flex items-center gap-2">
        <span className={`px-2 py-1 rounded text-sm ${company.is_active? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{company.is_active? 'Active':'Inactive'}</span>
        <button onClick={()=>onOpen(company.id)} className="px-3 py-1 bg-blue-600 text-white rounded">View / Edit</button>
        <button onClick={()=>onToggle(company.id)} className="px-3 py-1 bg-gray-200 rounded">Toggle</button>
      </div>
    </div>
  )
}

export default CompanyCard
