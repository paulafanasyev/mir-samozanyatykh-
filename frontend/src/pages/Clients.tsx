import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { Plus, Users, Mail, Phone } from 'lucide-react'
import toast from 'react-hot-toast'

interface Client {
  id: number
  name: string
  email: string | null
  phone: string | null
  company: string | null
  status: string
}

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/api/crm/clients').then((res) => { setClients(res.data); setLoading(false) })
      .catch(() => { toast.error('Ne udalos zagruzit klientov'); setLoading(false) })
  }, [])

  if (loading) return <div className="text-center py-12">Zagruzka...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Klienty</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"><Plus className="w-4 h-4" /> Dobavit</button>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {clients.map((c) => (
          <div key={c.id} className="bg-white p-5 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center"><Users className="w-5 h-5 text-blue-600" /></div>
              <div><h3 className="font-semibold text-slate-800">{c.name}</h3><span className="text-xs text-slate-500 uppercase">{c.status}</span></div>
            </div>
            {c.email && <div className="flex items-center gap-2 text-sm text-slate-600 mb-1"><Mail className="w-3 h-3" />{c.email}</div>}
            {c.phone && <div className="flex items-center gap-2 text-sm text-slate-600"><Phone className="w-3 h-3" />{c.phone}</div>}
          </div>
        ))}
      </div>
      {clients.length === 0 && <div className="text-center py-8 text-slate-500">Poka net klientov</div>}
    </div>
  )
}
