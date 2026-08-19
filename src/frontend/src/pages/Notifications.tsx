import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {

Bell, CheckCircle, XCircle, Trash2, CheckCheck,

Info, AlertTriangle, AlertOctagon, X,

Clock, ExternalLink, Filter
} from 'lucide-react'

interface Notification {

id: number

title: string

body: string

notification_type: string

is_read: boolean

action_url: string | null

data: Record<string, any> | null

created_at: string
}

export default function Notifications() {

const { user } = useAuthStore()

const [notifications, setNotifications] = useState<Notification[]>([])

const [unreadCount, setUnreadCount] = useState(0)

const [loading, setLoading] = useState(true)

const [error, setError] = useState('')

const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all')

const [typeFilter, setTypeFilter] = useState<string>('')


const fetchNotifications = async () => {

setLoading(true)

try {

const params = new URLSearchParams()

params.set('page', '1')

params.set('per_page', '100')

if (filter === 'unread') params.set('is_read', 'false')

if (filter === 'read') params.set('is_read', 'true')

if (typeFilter) params.set('notification_type', typeFilter)


const [notifRes, countRes] = await Promise.all([

api.get(`/api/notifications/?${params}`),

api.get('/api/notifications/unread-count'),

])

setNotifications(notifRes.data)

setUnreadCount(countRes.data.unread_count)

} catch (e: any) {

setError(e.response?.data?.message || 'Ошибка загрузки')

} finally {

setLoading(false)

}

}


useEffect(() => {

fetchNotifications()

}, [filter, typeFilter])


const markAsRead = async (id: number) => {

try {

await api.put(`/api/notifications/${id}/read`)

setNotifications(prev =>

prev.map(n => n.id === id ? { ...n, is_read: true } : n)

)

setUnreadCount(prev => Math.max(0, prev - 1))

} catch (e) {

// ignore

}

}


const markAllAsRead = async () => {

try {

await api.put('/api/notifications/read-all')

setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))

setUnreadCount(0)

} catch (e) {

// ignore

}

}


const deleteNotification = async (id: number) => {

try {

await api.delete(`/api/notifications/${id}`)

setNotifications(prev => prev.filter(n => n.id !== id))

} catch (e) {

// ignore

}

}


const deleteAllRead = async () => {

try {

await api.delete('/api/notifications/')

setNotifications(prev => prev.filter(n => !n.is_read))

} catch (e) {

// ignore

}

}


const typeIcons: Record<string, any> = {

info: Info,

success: CheckCircle,

warning: AlertTriangle,

error: AlertOctagon,

}


const typeColors: Record<string, string> = {

info: 'bg-orange-50 border-orange-200 text-orange-700',

success: 'bg-green-50 border-green-200 text-green-700',

warning: 'bg-amber-50 border-amber-200 text-amber-700',

error: 'bg-red-50 border-red-200 text-red-700',

}


const typeDotColors: Record<string, string> = {

info: 'bg-orange-500',

success: 'bg-green-500',

warning: 'bg-amber-500',

error: 'bg-red-500',

}


return (

<div className="space-y-6">

{/* Header */}

<div className="flex items-center justify-between">

<div>

<h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">

<Bell className="w-7 h-7 text-orange-600" />

Уведомления

{unreadCount > 0 && (

<span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">

{unreadCount}

</span>

)}

</h1>

<p className="text-slate-500 mt-1">Все уведомления и напоминания</p>

</div>

<div className="flex gap-2">

{unreadCount > 0 && (

<button

onClick={markAllAsRead}

className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700"

>

<CheckCheck className="w-4 h-4" />

Прочитать все

</button>

)}

<button

onClick={deleteAllRead}

className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50"

>

<Trash2 className="w-4 h-4" />

Удалить прочитанные

</button>

</div>

</div>


{error && (

<div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">

<AlertOctagon className="w-5 h-5" />

{error}

<button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>

</div>

)}


{/* Filters */}

<div className="flex flex-wrap gap-3">

<div className="flex bg-white rounded-lg border border-slate-200 overflow-hidden">

{(['all', 'unread', 'read'] as const).map((f) => (

<button

key={f}

onClick={() => setFilter(f)}

className={`px-4 py-2 text-sm font-medium transition-colors ${

filter === f

? 'bg-orange-600 text-white'

: 'text-slate-600 hover:bg-slate-50'

}`}

>

{f === 'all' ? 'Все' : f === 'unread' ? 'Непрочитанные' : 'Прочитанные'}

</button>

))}

</div>

<select

value={typeFilter}

onChange={(e) => setTypeFilter(e.target.value)}

className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-orange-500"

>

<option value="">Все типы</option>

<option value="info">Информация</option>

<option value="success">Успех</option>

<option value="warning">Предупреждение</option>

<option value="error">Ошибка</option>

</select>

</div>


{/* Notifications List */}

<div className="bg-white rounded-xl border border-slate-200 overflow-hidden">

{loading ? (

<div className="p-12 text-center text-slate-500">

<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto mb-3" />

Загрузка...

</div>

) : notifications.length === 0 ? (

<div className="p-12 text-center text-slate-500">

<Bell className="w-12 h-12 mx-auto mb-3 text-slate-300" />

<p>Уведомлений нет</p>

<p className="text-sm text-slate-400 mt-1">

{filter === 'unread' ? 'Все уведомления прочитаны' : 'Пока ничего не произошло'}

</p>

</div>

) : (

<div className="divide-y divide-slate-100">

{notifications.map((n) => {

const Icon = typeIcons[n.notification_type] || Info

return (

<div

key={n.id}

className={`p-4 hover:bg-slate-50 transition-colors ${

!n.is_read ? 'bg-orange-50/30' : ''

}`}

>

<div className="flex items-start gap-3">

<div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${

!n.is_read ? typeDotColors[n.notification_type] || 'bg-orange-500' : 'bg-transparent'

}`} />

<div className="flex-1 min-w-0">

<div className="flex items-center gap-2 mb-1">

<Icon className={`w-4 h-4 ${

n.notification_type === 'success' ? 'text-green-500' :

n.notification_type === 'warning' ? 'text-amber-500' :

n.notification_type === 'error' ? 'text-red-500' :

'text-orange-500'

}`} />

<span className="font-medium text-slate-900 text-sm">{n.title}</span>

{!n.is_read && (

<span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded font-medium">

Новое

</span>

)}

</div>

<p className="text-slate-600 text-sm mb-2">{n.body}</p>

<div className="flex items-center gap-3">

<span className="text-xs text-slate-400 flex items-center gap-1">

<Clock className="w-3 h-3" />

{new Date(n.created_at).toLocaleString('ru-RU')}

</span>

{n.action_url && (

<a

href={n.action_url}

className="text-xs text-orange-600 hover:text-orange-700 flex items-center gap-1"

>

<ExternalLink className="w-3 h-3" />

Перейти

</a>

)}

</div>

</div>

<div className="flex items-center gap-1 flex-shrink-0">

{!n.is_read && (

<button

onClick={() => markAsRead(n.id)}

className="p-1.5 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"

title="Отметить прочитанным"

>

<CheckCircle className="w-4 h-4" />

</button>

)}

<button

onClick={() => deleteNotification(n.id)}

className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"

title="Удалить"

>

<Trash2 className="w-4 h-4" />

</button>

</div>

</div>

</div>

)

})}

</div>

)}

</div>

</div>

)
}
