import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import {
TrendingUp, FileText, Users, Handshake, DollarSign,
Bell, CheckCircle, AlertCircle, ArrowRight, PlusCircle,
Receipt, Calculator, CalendarDays
} from 'lucide-react'

interface Stats {
total_invoices: number
total_revenue: number
clients_count: number
deals_count: number
won_deals: number
conversion_rate: number
tasks_pending: number
tasks_overdue: number
unread_notifications: number
total_call_duration: number
}
export default function Dashboard() {
const [stats, setStats] = useState<Stats | null>(null)
const [loading, setLoading] = useState(true)
useEffect(() => {
const fetchStats = async () => {
try {
const [salesRes, crmRes, notifRes] = await Promise.all([
apiClient.get('/api/sales/stats'),
apiClient.get('/api/crm/stats'),
apiClient.get('/api/notifications/unread-count'),
])
setStats({
total_invoices: salesRes.data.stats?.total_invoices || 0,
total_revenue: salesRes.data.stats?.total_revenue || 0,
clients_count: crmRes.data.clients_count || 0,
deals_count: crmRes.data.deals_count || 0,
won_deals: crmRes.data.won_deals || 0,
conversion_rate: crmRes.data.conversion_rate || 0,
tasks_pending: crmRes.data.tasks_pending || 0,
tasks_overdue: crmRes.data.tasks_overdue || 0,
unread_notifications: notifRes.data.unread_count || 0,
total_call_duration: crmRes.data.total_call_duration || 0,
})
} catch {
setStats({
total_invoices: 0, total_revenue: 0, clients_count: 0, deals_count: 0,
won_deals: 0, conversion_rate: 0, tasks_pending: 0, tasks_overdue: 0,
unread_notifications: 0, total_call_duration: 0
})
} finally {
setLoading(false)
}
}
fetchStats()
}, [])
if (loading) return <div className='text-center py-12'>Загрузка...</div>
return (
<div className='space-y-6'>
<div className='flex items-center justify-between'>
<h1 className='text-2xl font-bold text-slate-900'>Панель управления</h1>
<span className='text-sm text-slate-500'>v8.4.31</span>
</div>
{/* Stats Grid */}
<div className='grid sm:grid-cols-2 lg:grid-cols-4 gap-4'>
<StatCard icon={FileText} label='Счетов' value={stats?.total_invoices || 0} color='blue' link='/invoices' />
<StatCard icon={DollarSign} label='Выручка' value={`${(stats?.total_revenue || 0).toLocaleString('ru-RU')} ₽`} color='green' link='/invoices' />
<StatCard icon={Users} label='Клиентов' value={stats?.clients_count || 0} color='purple' link='/clients' />
<StatCard icon={Handshake} label='Сделок' value={stats?.deals_count || 0} color='orange' link='/deals' />
</div>
{/* Secondary Stats */}
<div className='grid sm:grid-cols-3 gap-4'>
<div className='bg-white p-4 rounded-xl border border-slate-200'>
<div className='flex items-center gap-2 mb-2'>
<TrendingUp className='w-4 h-4 text-emerald-500' />
<span className='text-sm text-slate-500'>Конверсия</span>
</div>
<p className='text-xl font-bold text-slate-900'>{stats?.conversion_rate || 0}%</p>
</div>
<div className='bg-white p-4 rounded-xl border border-slate-200'>
<div className='flex items-center gap-2 mb-2'>
<CheckCircle className='w-4 h-4 text-orange-500' />
<span className='text-sm text-slate-500'>Задач</span>
</div>
<p className='text-xl font-bold text-slate-900'>{stats?.tasks_pending || 0}</p>
</div>
<Link to='/notifications' className='bg-white p-4 rounded-xl border border-slate-200 hover:border-amber-300 transition-colors block'>
<div className='flex items-center gap-2 mb-2'>
<Bell className='w-4 h-4 text-amber-500' />
<span className='text-sm text-slate-500'>Уведомлений</span>
</div>
<p className='text-xl font-bold text-slate-900'>{stats?.unread_notifications || 0}</p>
</Link>
</div>
{/* Quick Actions */}
<div className='bg-white p-5 rounded-xl border border-slate-200'>
<h2 className='font-semibold text-slate-900 mb-4'>Быстрые действия</h2>
<div className='flex flex-wrap gap-3'>
<QuickAction to='/invoices' label='Создать счет' color='blue' icon={PlusCircle} />
<QuickAction to='/clients' label='Добавить клиента' color='purple' icon={Users} />
<QuickAction to='/deals' label='Новая сделка' color='orange' icon={Handshake} />
<QuickAction to='/tasks' label='Мои задачи' color='emerald' icon={CheckCircle} />
<QuickAction to='/calendar' label='Календарь' color='indigo' icon={CalendarDays} />
<QuickAction to='/accounting' label='Бухгалтерия' color='cyan' icon={Calculator} />
<QuickAction to='/receipt-check' label='Проверить чек' color='rose' icon={Receipt} />
</div>
</div>
{stats && stats.tasks_overdue > 0 && (
<div className='bg-red-50 border border-red-200 p-4 rounded-xl flex items-center gap-3'>
<AlertCircle className='w-5 h-5 text-red-500 flex-shrink-0' />
<p className='text-red-700'>У вас {stats.tasks_overdue} просроченных задач!</p>
<Link to='/tasks' className='ml-auto text-red-600 hover:underline text-sm font-medium'>Посмотреть →</Link>
</div>
)}
</div>
)
}
function StatCard({ icon: Icon, label, value, color, link }: { icon: any, label: string, value: string | number, color: string, link: string }) {
const colors: Record<string, string> = {
blue: 'bg-orange-50 text-orange-600',
green: 'bg-green-50 text-green-600',
purple: 'bg-amber-50 text-amber-600',
orange: 'bg-orange-50 text-orange-600',
emerald: 'bg-emerald-50 text-emerald-600',
indigo: 'bg-indigo-50 text-indigo-600',
cyan: 'bg-cyan-50 text-cyan-600',
rose: 'bg-rose-50 text-rose-600',
}
return (
<Link to={link} className='bg-white p-5 rounded-xl border border-slate-200 hover:border-orange-300 hover:shadow-sm transition-all block'>
<div className='flex items-center gap-3 mb-2'>
<div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colors[color]}`}>
<Icon className='w-4 h-4' />
</div>
<span className='text-sm text-slate-500'>{label}</span>
</div>
<p className='text-2xl font-bold text-slate-900'>{value}</p>
</Link>
)
}
function QuickAction({ to, label, color, icon: Icon }: { to: string, label: string, color: string, icon: any }) {
const colors: Record<string, string> = {
blue: 'bg-orange-600 hover:bg-orange-700',
purple: 'bg-amber-600 hover:bg-amber-700',
orange: 'bg-orange-600 hover:bg-orange-700',
emerald: 'bg-emerald-600 hover:bg-emerald-700',
indigo: 'bg-indigo-600 hover:bg-indigo-700',
cyan: 'bg-cyan-600 hover:bg-cyan-700',
rose: 'bg-rose-600 hover:bg-rose-700',
}
return (
<Link to={to} className={`${colors[color]} text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2`}>
<Icon className='w-4 h-4' />
{label}
</Link>
)
}