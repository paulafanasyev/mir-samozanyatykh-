import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { Plus, Handshake, TrendingUp } from 'lucide-react'
import toast from 'react-hot-toast'

interface Deal {
  id: number
  title: string
  amount: number | null
  status: string
  priority: string
  deadline: string | null
}

export default function Deals() {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/api/crm/deals').then((res) => { setDeals(res.data); setLoading(false) })
      .catch(() => { toast.error('Ne udalos zagruzit sdelki'); setLoading(false) })
  }, [])

  const priorityColor = (p: string) => ({ low: 'bg-slate-100 text-slate-600', medium: 'bg-blue-50 text-blue-600', high: 'bg-orange-50 text-orange-600', urgent: 'bg-red-50 text-red-600' }[p] || 'bg-slate-100')
  const statusColor = (s: string) => ({ new: 'bg-slate-100', contacted: 'bg-blue-50', proposal: 'bg-purple-50', negotiation: 'bg-orange-50', won: 'bg-green-50', lost: 'bg-red-50' }[s] || 'bg-slate-100')

  if (loading) return <div className="text-center py-12">Zagruzka...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Sdelki</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"><Plus className="w-4 h-4" /> Novaya sdelka</button>
      </div>
      <div className="space-y-3">
        {deals.map((d) => (
          <div key={d.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between hover:shadow-sm transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center"><Handshake className="w-5 h-5 text-blue-600" /></div>
              <div><h3 className="font-medium text-slate-800">{d.title}</h3><div className="flex items-center gap-2 mt-1"><span className={`text-xs px-2 py-0.5 rounded-full ${statusColor(d.status)}`}>{d.status}</span><span className={`text-xs px-2 py-0.5 rounded-full ${priorityColor(d.priority)}`}>{d.priority}</span></div></div>
            </div>
            <div className="text-right"><div className="font-semibold text-slate-800">{d.amount ? `${d.amount} ₽` : '—'}</div>{d.deadline && <div className="text-xs text-slate-500">{new Date(d.deadline).toLocaleDateString('ru-RU')}</div>}</div>
          </div>
        ))}
      </div>
      {deals.length === 0 && <div className="text-center py-8 text-slate-500">Poka net sdelok</div>}
    </div>
  )
}
