import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {

Eye, Search, Filter, Calendar, Clock, User,

ChevronLeft, ChevronRight, X, CheckCircle, XCircle,

ArrowLeft, Shield, FileText, Globe
} from 'lucide-react'

interface AuditLog {

id: number

user_id: number | null

user_email: string | null

action: string

resource: string | null

details: string | null

ip_address: string | null

user_agent: string | null

success: boolean

created_at: string
}

interface AuditAction {

action: string

count: number
}

export default function AuditLogs() {

const { user } = useAuthStore()

const navigate = useNavigate()

const [searchParams] = useSearchParams()

const [logs, setLogs] = useState<AuditLog[]>([])

const [actions, setActions] = useState<AuditAction[]>([])

const [loading, setLoading] = useState(false)

const [error, setError] = useState('')

const [page, setPage] = useState(1)

const [totalPages, setTotalPages] = useState(1)

const [search, setSearch] = useState('')

const [actionFilter, setActionFilter] = useState(searchParams.get('action') || '')

const [userIdFilter, setUserIdFilter] = useState(searchParams.get('user_id') || '')

const [startDate, setStartDate] = useState('')

const [endDate, setEndDate] = useState('')

const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)


// Redirect non-admins/moderators

useEffect(() => {

if (user && !user.is_admin && !user.is_moderator) {

navigate('/dashboard')

}

}, [user, navigate])


const fetchLogs = async () => {

setLoading(true)

try {

const params = new URLSearchParams()

params.set('page', String(page))

params.set('per_page', '50')

if (search) params.set('search', search)

if (actionFilter) params.set('action', actionFilter)

if (userIdFilter) params.set('user_id', userIdFilter)

if (startDate) params.set('start_date', new Date(startDate).toISOString())

if (endDate) params.set('end_date', new Date(endDate).toISOString())


const res = await api.get(`/api/admin/audit-logs?${params}`)

setLogs(res.data.logs)

setTotalPages(res.data.pagination.total_pages)

} catch (e: any) {

setError(e.response?.data?.message || 'Ошибка загрузки логов')

} finally {

setLoading(false)

}

}


const fetchActions = async () => {

try {

const res = await api.get('/api/admin/audit-logs/actions')

setActions(res.data)

} catch (e) {

// silently fail

}

}


useEffect(() => {

fetchLogs()

fetchActions()

}, [page, search, actionFilter, userIdFilter, startDate, endDate])


const actionColors: Record<string, string> = {

register: 'bg-green-100 text-green-700',

login: 'bg-orange-100 text-orange-700',

login_failed: 'bg-red-100 text-red-700',

logout: 'bg-slate-100 text-slate-700',

profile_updated: 'bg-cyan-100 text-cyan-700',

password_changed: 'bg-orange-100 text-orange-700',

password_reset: 'bg-amber-100 text-amber-700',

email_verified: 'bg-emerald-100 text-emerald-700',

'2fa_enabled': 'bg-amber-100 text-amber-700',

'2fa_disabled': 'bg-pink-100 text-pink-700',

product_created: 'bg-indigo-100 text-indigo-700',

product_updated: 'bg-amber-100 text-amber-700',

product_deleted: 'bg-rose-100 text-rose-700',

invoice_created: 'bg-teal-100 text-teal-700',

invoice_sent: 'bg-sky-100 text-sky-700',

payment_created: 'bg-lime-100 text-lime-700',

yookassa_payment_created: 'bg-emerald-100 text-emerald-700',

subscription_upgraded: 'bg-amber-100 text-amber-700',

admin_users_list: 'bg-red-100 text-red-700',

admin_user_view: 'bg-red-100 text-red-700',

admin_user_updated: 'bg-red-100 text-red-700',

admin_user_blocked: 'bg-red-100 text-red-700',

admin_user_unblocked: 'bg-green-100 text-green-700',

admin_user_deleted: 'bg-red-100 text-red-700',

admin_bulk_tier_update: 'bg-amber-100 text-amber-700',

admin_stats_viewed: 'bg-orange-100 text-orange-700',

admin_audit_logs_viewed: 'bg-orange-100 text-orange-700',

admin_user_audit_viewed: 'bg-orange-100 text-orange-700',

admin_sessions_revoked: 'bg-orange-100 text-orange-700',

}


const getActionColor = (action: string) => {

return actionColors[action] || 'bg-slate-100 text-slate-700'

}


const formatDate = (dateStr: string) => {

const d = new Date(dateStr)

return d.toLocaleString('ru-RU', {

day: '2-digit',

month: '2-digit',

year: 'numeric',

hour: '2-digit',

minute: '2-digit',

second: '2-digit',

})

}


const clearFilters = () => {

setSearch('')

setActionFilter('')

setUserIdFilter('')

setStartDate('')

setEndDate('')

setPage(1)

}


return (

<div className="space-y-6">

{/* Header */}

<div className="flex items-center justify-between">

<div className="flex items-center gap-3">

<button

onClick={() => navigate('/admin')}

className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"

>

<ArrowLeft className="w-5 h-5" />

</button>

<div>

<h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">

<Eye className="w-7 h-7 text-orange-600" />

Аудит-логи

</h1>

<p className="text-slate-500 mt-1">История всех действий на платформе</p>

</div>

</div>

<div className="flex items-center gap-2">

<span className="text-sm text-slate-500">

{logs.length} записей

</span>

</div>

</div>


{error && (

<div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">

<XCircle className="w-5 h-5" />

{error}

<button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>

</div>

)}


{/* Filters */}

<div className="bg-white rounded-xl border border-slate-200 p-4 space-y-3">

<div className="flex flex-wrap gap-3">

<div className="flex-1 min-w-[200px] relative">

<Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

<input

type="text"

placeholder="Поиск по деталям..."

value={search}

onChange={(e) => { setSearch(e.target.value); setPage(1) }}

className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500"

/>

</div>

<select

value={actionFilter}

onChange={(e) => { setActionFilter(e.target.value); setPage(1) }}

className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 min-w-[180px]"

>

<option value="">Все действия</option>

{actions.map((a) => (

<option key={a.action} value={a.action}>

{a.action} ({a.count})

</option>

))}

</select>

<input

type="text"

placeholder="ID пользователя"

value={userIdFilter}

onChange={(e) => { setUserIdFilter(e.target.value); setPage(1) }}

className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 w-32"

/>

<input

type="date"

value={startDate}

onChange={(e) => { setStartDate(e.target.value); setPage(1) }}

className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"

/>

<input

type="date"

value={endDate}

onChange={(e) => { setEndDate(e.target.value); setPage(1) }}

className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"

/>

<button

onClick={clearFilters}

className="px-3 py-2 text-slate-500 hover:text-slate-700 text-sm border border-slate-200 rounded-lg hover:bg-slate-50"

>

Сбросить

</button>

</div>

</div>


{/* Logs Table */}

<div className="bg-white rounded-xl border border-slate-200 overflow-hidden">

{loading ? (

<div className="p-12 text-center text-slate-500">

<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-3" />

Загрузка...

</div>

) : logs.length === 0 ? (

<div className="p-12 text-center text-slate-500">

<FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />

<p>Логи не найдены</p>

<p className="text-sm text-slate-400 mt-1">Попробуйте изменить фильтры</p>

</div>

) : (

<>

<div className="overflow-x-auto">

<table className="w-full text-sm">

<thead className="bg-slate-50 border-b border-slate-200">

<tr>

<th className="px-4 py-3 text-left font-medium text-slate-600 w-12">ID</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">Действие</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">Пользователь</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">Детали</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">IP</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">Время</th>

<th className="px-4 py-3 text-left font-medium text-slate-600">Статус</th>

</tr>

</thead>

<tbody className="divide-y divide-slate-100">

{logs.map((log) => (

<tr

key={log.id}

className="hover:bg-slate-50 transition-colors cursor-pointer"

onClick={() => setSelectedLog(log)}

>

<td className="px-4 py-3 text-slate-400 text-xs">#{log.id}</td>

<td className="px-4 py-3">

<span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getActionColor(log.action)}`}>

{log.action}

</span>

</td>

<td className="px-4 py-3">

{log.user_id ? (

<div className="flex items-center gap-2">

<User className="w-3 h-3 text-slate-400" />

<div>

<div className="text-slate-900 text-xs">{log.user_email || `ID: ${log.user_id}`}</div>

<div className="text-slate-400 text-xs">#{log.user_id}</div>

</div>

</div>

) : (

<span className="text-slate-400 text-xs">Система</span>

)}

</td>

<td className="px-4 py-3">

<div className="max-w-[200px] truncate text-slate-600 text-xs" title={log.details || ''}>

{log.details || '—'}

</div>

{log.resource && (

<div className="text-slate-400 text-xs mt-0.5">{log.resource}</div>

)}

</td>

<td className="px-4 py-3">

<div className="flex items-center gap-1 text-slate-500 text-xs">

<Globe className="w-3 h-3" />

{log.ip_address || '—'}

</div>

</td>

<td className="px-4 py-3">

<div className="flex items-center gap-1 text-slate-500 text-xs">

<Clock className="w-3 h-3" />

{formatDate(log.created_at)}

</div>

</td>

<td className="px-4 py-3">

{log.success ? (

<CheckCircle className="w-4 h-4 text-green-500" />

) : (

<XCircle className="w-4 h-4 text-red-500" />

)}

</td>

</tr>

))}

</tbody>

</table>

</div>


{/* Pagination */}

<div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">

<span className="text-sm text-slate-500">

Страница {page} из {totalPages}

</span>

<div className="flex gap-2">

<button

onClick={() => setPage(p => Math.max(1, p - 1))}

disabled={page === 1}

className="p-2 rounded-lg border border-slate-200 disabled:opacity-50 hover:bg-slate-50"

>

<ChevronLeft className="w-4 h-4" />

</button>

<button

onClick={() => setPage(p => Math.min(totalPages, p + 1))}

disabled={page === totalPages}

className="p-2 rounded-lg border border-slate-200 disabled:opacity-50 hover:bg-slate-50"

>

<ChevronRight className="w-4 h-4" />

</button>

</div>

</div>

</>

)}

</div>


{/* Detail Modal */}

{selectedLog && (

<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">

<div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4">

<div className="flex items-center justify-between">

<h3 className="text-lg font-semibold flex items-center gap-2">

<Shield className="w-5 h-5 text-orange-600" />

Детали записи #{selectedLog.id}

</h3>

<button onClick={() => setSelectedLog(null)}><X className="w-5 h-5 text-slate-400" /></button>

</div>


<div className="space-y-3 text-sm">

<div className="flex justify-between py-2 border-b border-slate-100">

<span className="text-slate-500">Действие</span>

<span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getActionColor(selectedLog.action)}`}>

{selectedLog.action}

</span>

</div>

<div className="flex justify-between py-2 border-b border-slate-100">

<span className="text-slate-500">Пользователь</span>

<span className="text-slate-900">

{selectedLog.user_email || `ID: ${selectedLog.user_id}` || 'Система'}

</span>

</div>

<div className="flex justify-between py-2 border-b border-slate-100">

<span className="text-slate-500">Ресурс</span>

<span className="text-slate-900">{selectedLog.resource || '—'}</span>

</div>

<div className="py-2 border-b border-slate-100">

<span className="text-slate-500 block mb-1">Детали</span>

<div className="bg-slate-50 rounded-lg p-3 text-slate-700 text-xs font-mono break-all">

{selectedLog.details || '—'}

</div>

</div>

<div className="flex justify-between py-2 border-b border-slate-100">

<span className="text-slate-500">IP адрес</span>

<span className="text-slate-900 font-mono text-xs">{selectedLog.ip_address || '—'}</span>

</div>

<div className="py-2 border-b border-slate-100">

<span className="text-slate-500 block mb-1">User-Agent</span>

<div className="text-slate-700 text-xs break-all">

{selectedLog.user_agent || '—'}

</div>

</div>

<div className="flex justify-between py-2 border-b border-slate-100">

<span className="text-slate-500">Статус</span>

<span className={`flex items-center gap-1 ${selectedLog.success ? 'text-green-600' : 'text-red-600'}`}>

{selectedLog.success ? (

<><CheckCircle className="w-4 h-4" /> Успешно</>

) : (

<><XCircle className="w-4 h-4" /> Ошибка</>

)}

</span>

</div>

<div className="flex justify-between py-2">

<span className="text-slate-500">Время</span>

<span className="text-slate-900">{formatDate(selectedLog.created_at)}</span>

</div>

</div>


<div className="flex gap-3 pt-2">

{selectedLog.user_id && (

<button

onClick={() => {

setSelectedLog(null)

navigate(`/api/admin/audit-logs?user_id=${selectedLog.user_id}`)

}}

className="flex-1 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700"

>

Все логи пользователя

</button>

)}

<button

onClick={() => setSelectedLog(null)}

className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"

>

Закрыть

</button>

</div>

</div>

</div>

)}

</div>

)
}
