import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { Plus, Users, Mail, Phone, Building2, Search, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'

interface Client {
id: number
name: string
email: string | null
phone: string | null
company: string | null
inn: string | null
notes: string | null
status: string
created_at: string
}
export default function Clients() {
const [clients, setClients] = useState<Client[]>([])
const [loading, setLoading] = useState(true)
const [search, setSearch] = useState('')
const [showForm, setShowForm] = useState(false)
const [form, setForm] = useState({ name: '', email: '', phone: '', company: '', inn: '', notes: '' })
useEffect(() => {
fetchClients()
}, [])
const fetchClients = async () => {
try {
const res = await apiClient.get('/api/crm/clients')
setClients(res.data)
} catch {
toast.error('Не удалось загрузить клиентов')
} finally {
setLoading(false)
}
}
const handleCreate = async (e: FormEvent) => {
e.preventDefault()
try {
await apiClient.post('/api/crm/clients', form)
toast.success('Клиент добавлен')
setShowForm(false)
setForm({ name: '', email: '', phone: '', company: '', inn: '', notes: '' })
fetchClients()
} catch {
toast.error('Ошибка создания клиента')
}
}
const filtered = clients.filter(c =>
c.name.toLowerCase().includes(search.toLowerCase()) ||
c.email?.toLowerCase().includes(search.toLowerCase()) ||
c.company?.toLowerCase().includes(search.toLowerCase())
)
if (loading) return <div className='text-center py-12'>Загрузка...</div>
return (
<div className='space-y-6'>
<div className='flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4'>
<h1 className='text-2xl font-bold text-slate-900'>Клиенты</h1>
<button onClick={() => setShowForm(true)} className='bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-orange-700 transition-colors'>
<Plus className='w-4 h-4' /> Добавить клиента
</button>
</div>
{/* Search */}
<div className='relative'>
<Search className='absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400' />
<input
type='text'
placeholder='Поиск по имени, email или компании...'
value={search}
onChange={(e) => setSearch(e.target.value)}
className='w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none'
/>
{search && (
<button onClick={() => setSearch('')} className='absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600'>
<X className='w-4 h-4' />
</button>
)}
</div>
{/* Add Form */}
{showForm && (
<div className='bg-white p-5 rounded-xl border border-slate-200'>
<div className='flex justify-between items-center mb-4'>
<h3 className='font-semibold text-slate-900'>Новый клиент</h3>
<button onClick={() => setShowForm(false)} className='text-slate-400 hover:text-slate-600'>
<X className='w-4 h-4' />
</button>
</div>
<form onSubmit={handleCreate} className='grid sm:grid-cols-2 gap-4'>
<input type='text' placeholder='Имя *' required value={form.name} onChange={e => setForm({...form, name: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='email' placeholder='Email' value={form.email} onChange={e => setForm({...form, email: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='tel' placeholder='Телефон' value={form.phone} onChange={e => setForm({...form, phone: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='text' placeholder='Компания' value={form.company} onChange={e => setForm({...form, company: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='text' placeholder='ИНН' value={form.inn} onChange={e => setForm({...form, inn: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<input type='text' placeholder='Примечания' value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} className='px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 outline-none' />
<div className='sm:col-span-2'>
<button type='submit' className='bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2'>
<Check className='w-4 h-4' /> Сохранить
</button>
</div>
</form>
</div>
)}
{/* Clients Grid */}
<div className='grid sm:grid-cols-2 lg:grid-cols-3 gap-4'>
{filtered.map((c) => (
<div key={c.id} className='bg-white p-5 rounded-xl border border-slate-200 hover:shadow-md hover:border-orange-200 transition-all'>
<div className='flex items-center gap-3 mb-3'>
<div className='w-10 h-10 bg-gradient-to-br from-orange-50 to-orange-100 rounded-full flex items-center justify-center'>
<Users className='w-5 h-5 text-orange-600' />
</div>
<div className='flex-1 min-w-0'>
<h3 className='font-semibold text-slate-800 truncate'>{c.name}</h3>
<span className={`text-xs px-2 py-0.5 rounded-full ${c.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
{c.status === 'active' ? 'Активен' : c.status}
</span>
</div>
</div>
<div className='space-y-1.5'>
{c.email && <div className='flex items-center gap-2 text-sm text-slate-600'><Mail className='w-3.5 h-3.5 text-slate-400' />{c.email}</div>}
{c.phone && <div className='flex items-center gap-2 text-sm text-slate-600'><Phone className='w-3.5 h-3.5 text-slate-400' />{c.phone}</div>}
{c.company && <div className='flex items-center gap-2 text-sm text-slate-600'><Building2 className='w-3.5 h-3.5 text-slate-400' />{c.company}</div>}
{c.inn && <div className='text-xs text-slate-400'>ИНН: {c.inn}</div>}
</div>
</div>
))}
</div>
{filtered.length === 0 && (
<div className='text-center py-12'>
<Users className='w-12 h-12 text-slate-300 mx-auto mb-3' />
<p className='text-slate-500'>{search ? 'Клиенты не найдены' : 'Пока нет клиентов'}</p>
</div>
)}
</div>
)
}