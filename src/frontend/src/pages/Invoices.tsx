import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import apiClient from '../api/client'
import { Plus, FileText, Search, X, Check, Download, Eye } from 'lucide-react'
import toast from 'react-hot-toast'

interface Invoice {
id: number
invoice_number: string
total_amount: number
status: string
due_date: string | null
paid_at: string | null
client_id: number | null
created_at: string
}
export default function Invoices() {
const [invoices, setInvoices] = useState<Invoice[]>([])
const [loading, setLoading] = useState(true)
const [search, setSearch] = useState('')
const [filterStatus, setFilterStatus] = useState('')
const [showForm, setShowForm] = useState(false)
const [clients, setClients] = useState<Array<{id:number; name:string}>>([])
const [form, setForm] = useState({ client_id: '', description: '', quantity: '1', unit_price: '', due_date: '', notes: '' })
useEffect(() => {
fetchInvoices()
apiClient.get('/api/crm/clients').then(r => setClients(Array.isArray(r.data) ? r.data : [])).catch(() => setClients([]))
}, [])
const fetchInvoices = async () => {
try {
const res = await apiClient.get('/api/sales/invoices')
setInvoices(Array.isArray(res.data) ? res.data : (res.data?.invoices || []))
} catch {
toast.error('Не удалось загрузить счета')
} finally {
setLoading(false)
}
}
const handleCreate = async (e: FormEvent) => {
e.preventDefault()
try {
if (!form.client_id || !form.description || !form.unit_price) {
throw new Error('Заполните клиента, описание и стоимость')
}
await apiClient.post('/api/sales/invoices', {
client_id: Number(form.client_id),
due_date: form.due_date || null,
notes: form.notes || null,
items: [{ description: form.description, quantity: Number(form.quantity) || 1, unit_price: Number(form.unit_price) }],
})
toast.success('Счет создан')
setShowForm(false)
setForm({ client_id: '', description: '', quantity: '1', unit_price: '', due_date: '', notes: '' })
fetchInvoices()
} catch {
toast.error('Ошибка создания счета')
}
}
const getStatusBadge = (status: string) => {
const badges: Record<string, string> = {
draft: 'bg-slate-100 text-slate-600',
sent: 'bg-orange-100 text-orange-700',
paid: 'bg-green-100 text-green-700',
overdue: 'bg-red-100 text-red-700',
cancelled: 'bg-gray-100 text-gray-600',
}
const labels: Record<string, string> = {
draft: 'Черновик', sent: 'Отправлен', paid: 'Оплачен', overdue: 'Просрочен', cancelled: 'Отменен',
}
return { class: badges[status] || badges.draft, label: labels[status] || status }
}
const filtered = invoices.filter(inv => {
const matchSearch = inv.invoice_number.toLowerCase().includes(search.toLowerCase())
const matchStatus = !filterStatus || inv.status === filterStatus
return matchSearch && matchStatus
})
if (loading) return <div className='text-center py-12'>Загрузка...</div>
return (
<div className='space-y-6'>
<div className='flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4'>
<h1 className='text-2xl font-bold text-slate-900'>Счета</h1>
<button onClick={() => setShowForm(true)} className='bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-orange-700 transition-colors'>
<Plus className='w-4 h-4' /> Создать счет
</button>
</div>
{/* Filters */}
<div className='flex flex-col sm:flex-row gap-3'>
<div className='relative flex-1'>
<Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400' />
<input type='text' placeholder='Поиск по номеру...' value={search} onChange={e => setSearch(e.target.value)}
className='w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
{search && <button onClick={() => setSearch('')} className='absolute right-3 top-1/2 -translate-y-1/2 text-slate-400'><X className='w-4 h-4' /></button>}
</div>
<select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'>
<option value=''>Все статусы</option>
<option value='draft'>Черновик</option>
<option value='sent'>Отправлен</option>
<option value='paid'>Оплачен</option>
<option value='overdue'>Просрочен</option>
</select>
</div>
{/* Add Form */}
{showForm && (
<div className='bg-white p-5 rounded-xl border border-slate-200'>
<div className='flex justify-between items-center mb-4'>
<h3 className='font-semibold text-slate-900'>Новый счет</h3>
<button onClick={() => setShowForm(false)} className='text-slate-400 hover:text-slate-600'><X className='w-4 h-4' /></button>
</div>
<form onSubmit={handleCreate} className='grid sm:grid-cols-2 gap-4'>
<select required value={form.client_id} onChange={e => setForm({...form, client_id: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none'><option value=''>Выберите клиента *</option>{clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
<input type='text' placeholder='Описание услуги *' required value={form.description} onChange={e => setForm({...form, description: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='number' min='0.01' step='0.01' placeholder='Цена *' required value={form.unit_price} onChange={e => setForm({...form, unit_price: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='number' min='1' step='1' placeholder='Количество' required value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='date' placeholder='Срок оплаты' value={form.due_date} onChange={e => setForm({...form, due_date: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='text' placeholder='Примечания' value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<div className='sm:col-span-2'>
<button type='submit' className='bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2'>
<Check className='w-4 h-4' /> Создать счет
</button>
</div>
</form>
</div>
)}
{/* Stats */}
<div className='grid grid-cols-3 gap-4'>
<div className='bg-white p-4 rounded-xl border border-slate-200 text-center'>
<p className='text-2xl font-bold text-slate-900'>{invoices.filter(i => i.status === 'paid').length}</p>
<p className='text-xs text-slate-500 mt-1'>Оплачено</p>
</div>
<div className='bg-white p-4 rounded-xl border border-slate-200 text-center'>
<p className='text-2xl font-bold text-slate-900'>{invoices.filter(i => i.status === 'overdue').length}</p>
<p className='text-xs text-slate-500 mt-1'>Просрочено</p>
</div>
<div className='bg-white p-4 rounded-xl border border-slate-200 text-center'>
<p className='text-2xl font-bold text-slate-900'>{invoices.reduce((sum, i) => sum + (i.status === 'paid' ? i.total_amount : 0), 0).toLocaleString('ru-RU')} ₽</p>
<p className='text-xs text-slate-500 mt-1'>Всего получено</p>
</div>
</div>
{/* Invoices List */}
<div className='bg-white rounded-xl border border-slate-200 overflow-hidden'>
<div className='overflow-x-auto'>
<table className='w-full'>
<thead className='bg-slate-50 border-b border-slate-200'>
<tr>
<th className='text-left text-xs font-medium text-slate-500 uppercase px-4 py-3'>Номер</th>
<th className='text-left text-xs font-medium text-slate-500 uppercase px-4 py-3'>Сумма</th>
<th className='text-left text-xs font-medium text-slate-500 uppercase px-4 py-3'>Статус</th>
<th className='text-left text-xs font-medium text-slate-500 uppercase px-4 py-3'>Срок</th>
<th className='text-left text-xs font-medium text-slate-500 uppercase px-4 py-3'>Действия</th>
</tr>
</thead>
<tbody className='divide-y divide-slate-100'>
{filtered.map(inv => {
const status = getStatusBadge(inv.status)
return (
<tr key={inv.id} className='hover:bg-slate-50 transition-colors'>
<td className='px-4 py-3'>
<div className='flex items-center gap-2'>
<FileText className='w-4 h-4 text-slate-400' />
<span className='font-medium text-slate-800 text-sm'>{inv.invoice_number}</span>
</div>
</td>
<td className='px-4 py-3 font-semibold text-slate-800'>{inv.total_amount.toLocaleString('ru-RU')} ₽</td>
<td className='px-4 py-3'><span className={`text-xs px-2 py-0.5 rounded-full ${status.class}`}>{status.label}</span></td>
<td className='px-4 py-3 text-sm text-slate-500'>{inv.due_date ? new Date(inv.due_date).toLocaleDateString('ru-RU') : '—'}</td>
<td className='px-4 py-3'>
<div className='flex items-center gap-2'>
<button onClick={async () => { try { const r = await apiClient.get(`/api/sales/invoices/${inv.id}/pdf`, { responseType: 'blob' }); const url = URL.createObjectURL(r.data); window.open(url, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(url), 60000) } catch { toast.error('Не удалось открыть PDF') } }} className='p-1.5 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors' title='Просмотр'>
<Eye className='w-4 h-4' />
</button>
<button onClick={async () => { try { const r = await apiClient.get(`/api/sales/invoices/${inv.id}/pdf`, { responseType: 'blob' }); const url = URL.createObjectURL(r.data); const a = document.createElement('a'); a.href = url; a.download = `${inv.invoice_number}.pdf`; a.click(); URL.revokeObjectURL(url) } catch { toast.error('Не удалось скачать PDF') } }} className='p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors' title='Скачать PDF'>
<Download className='w-4 h-4' />
</button>
</div>
</td>
</tr>
)
})}
</tbody>
</table>
</div>
{filtered.length === 0 && (
<div className='text-center py-12'>
<FileText className='w-12 h-12 text-slate-300 mx-auto mb-3' />
<p className='text-slate-500'>{search || filterStatus ? 'Счета не найдены' : 'Пока нет счетов'}</p>
</div>
)}
</div>
</div>
)
}