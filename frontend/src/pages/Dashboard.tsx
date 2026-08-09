import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { TrendingUp, FileText, Users, Handshake, DollarSign } from 'lucide-react'

interface Stats {
  total_invoices: number
  total_revenue: number
  clients_count: number
  deals_count: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [salesRes, crmRes] = await Promise.all([
          apiClient.get('/api/sales/stats'),
          apiClient.get('/api/crm/stats'),
        ])
        setStats({
          total_invoices: salesRes.data.stats?.total_invoices || 0,
          total_revenue: salesRes.data.stats?.total_revenue || 0,
          clients_count: crmRes.data.clients_count || 0,
          deals_count: crmRes.data.deals_count || 0,
        })
      } catch {
        setStats({ total_invoices: 0, total_revenue: 0, clients_count: 0, deals_count: 0 })
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  if (loading) return <div className="text-center py-12">Zagruzka...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={FileText} label="Schetov" value={stats?.total_invoices || 0} color="blue" />
        <StatCard icon={DollarSign} label="Vyruchka" value={`${stats?.total_revenue || 0} ₽`} color="green" />
        <StatCard icon={Users} label="Klientov" value={stats?.clients_count || 0} color="purple" />
        <StatCard icon={Handshake} label="Sdelok" value={stats?.deals_count || 0} color="orange" />
      </div>
    </div>
  )
}

function StatCard({ icon: Icon, label, value, color }: { icon: any, label: string, value: string | number, color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
  }
  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="text-sm text-slate-500">{label}</span>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
    </div>
  )
}
