import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { Plus, FileText, CheckCircle, Clock, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface Invoice {
  id: number
  invoice_number: string
  total_amount: number
  status: string
  due_date: string | null
  paid_at: string | null
  created_at: string
}

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiClient.get('/api/sales/invoices').then((res) => {
      setInvoices(res.data)
      setLoading(false)
    }).catch(() => {
      toast.error('Ne udalos zagruzit scheta')
      setLoading(false)
    })
  }, [])

  const statusIcon = (status: string) => {
    switch (status) {
      case 'paid': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'sent': return <Clock className="w-4 h-4 text-yellow-500" />
      case 'draft': return <FileText className="w-4 h-4 text-slate-400" />
      default: return <XCircle className="w-4 h-4 text-red-500" />
    }
  }

  const statusLabel = (status: string) => {
    const labels: Record<string, string> = { draft: 'Chernovik', sent: 'Otpravlen', paid: 'Oplachen', cancelled: 'Otmenen', overdue: 'Prosrochen' }
    return labels[status] || status
  }

  if (loading) return <div className="text-center py-12">Zagruzka...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Scheta</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus className="w-4 h-4" /> Novyy schet
        </button>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr><th className="px-4 py-3 text-left font-medium text-slate-600">Nomer</th><th className="px-4 py-3 text-left font-medium text-slate-600">Summa</th><th className="px-4 py-3 text-left font-medium text-slate-600">Status</th><th className="px-4 py-3 text-left font-medium text-slate-600">Data</th></tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                <td className="px-4 py-3">{inv.total_amount} ₽</td>
                <td className="px-4 py-3"><div className="flex items-center gap-1">{statusIcon(inv.status)}<span>{statusLabel(inv.status)}</span></div></td>
                <td className="px-4 py-3 text-slate-500">{new Date(inv.created_at).toLocaleDateString('ru-RU')}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {invoices.length === 0 && <div className="text-center py-8 text-slate-500">Poka net schetov</div>}
      </div>
    </div>
  )
}
