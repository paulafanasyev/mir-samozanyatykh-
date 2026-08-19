import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {

ChevronLeft, ChevronRight, Calendar, Clock, MapPin,

Plus, X, CheckCircle2, AlertTriangle, User, Briefcase,

CalendarDays, CalendarRange, Calendar as CalendarIcon
} from 'lucide-react'

interface CalendarEvent {

id: number

title: string

description: string | null

event_type: string

start_time: string

end_time: string | null

all_day: boolean

location: string | null

client_name: string | null

deal_title: string | null

task_title: string | null

color: string | null
}

interface CalendarDay {

date: string

events: CalendarEvent[]

tasks_due: { id: number; title: string; priority: string; status: string }[]
}

interface TodaySummary {

date: string

events: CalendarEvent[]

tasks_due: { id: number; title: string; priority: string; status: string }[]

overdue: { id: number; title: string; priority: string; days_overdue: number }[]

total_events: number

total_tasks: number

total_overdue: number
}

export default function CalendarPage() {

const { user } = useAuthStore()

const [currentDate, setCurrentDate] = useState(new Date())

const [days, setDays] = useState<CalendarDay[]>([])

const [todaySummary, setTodaySummary] = useState<TodaySummary | null>(null)

const [loading, setLoading] = useState(true)

const [error, setError] = useState('')

const [viewMode, setViewMode] = useState<'month' | 'week' | 'today'>('month')

const [selectedDay, setSelectedDay] = useState<string | null>(null)

const [showCreate, setShowCreate] = useState(false)


const [newEvent, setNewEvent] = useState({

title: '',

description: '',

event_type: 'meeting',

start_time: '',

end_time: '',

all_day: false,

location: '',

color: '#3B82F6',

})


const year = currentDate.getFullYear()

const month = currentDate.getMonth() + 1


const fetchMonth = async () => {

setLoading(true)

try {

const res = await api.get(`/api/calendar/view/month?year=${year}&month=${month}`)

setDays(res.data.days)

} catch (e: any) {

setError(e.response?.data?.message || 'Ошибка загрузки')

} finally {

setLoading(false)

}

}


const fetchToday = async () => {

try {

const res = await api.get('/api/calendar/today')

setTodaySummary(res.data)

} catch (e) {

// ignore

}

}


useEffect(() => {

if (viewMode === 'month') fetchMonth()

fetchToday()

}, [currentDate, viewMode])


const createEvent = async () => {

if (!newEvent.title.trim()) return

try {

await api.post('/api/calendar/events', {

...newEvent,

start_time: new Date(newEvent.start_time).toISOString(),

end_time: newEvent.end_time ? new Date(newEvent.end_time).toISOString() : null,

})

setShowCreate(false)

setNewEvent({ title: '', description: '', event_type: 'meeting', start_time: '', end_time: '', all_day: false, location: '', color: '#3B82F6' })

fetchMonth()

fetchToday()

} catch (e: any) {

setError(e.response?.data?.message || 'Ошибка создания')

}

}


const prevMonth = () => {

setCurrentDate(new Date(year, month - 2, 1))

}


const nextMonth = () => {

setCurrentDate(new Date(year, month, 1))

}


const monthNames = [

'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',

'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'

]


const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


const eventTypeColors: Record<string, string> = {

meeting: 'bg-orange-500',

call: 'bg-green-500',

task: 'bg-amber-500',

deadline: 'bg-red-500',

reminder: 'bg-amber-500',

other: 'bg-slate-500',

}


const eventTypeLabels: Record<string, string> = {

meeting: 'Встреча',

call: 'Звонок',

task: 'Задача',

deadline: 'Дедлайн',

reminder: 'Напоминание',

other: 'Другое',

}


const priorityColors: Record<string, string> = {

low: 'bg-slate-200',

medium: 'bg-orange-200',

high: 'bg-orange-200',

urgent: 'bg-red-200',

}


const selectedDayData = days.find(d => d.date === selectedDay)


return (

<div className="space-y-6">

{/* Header */}

<div className="flex items-center justify-between flex-wrap gap-3">

<div>

<h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">

<CalendarIcon className="w-7 h-7 text-orange-600" />

Календарь

</h1>

<p className="text-slate-500 mt-1">События, задачи и дедлайны</p>

</div>

<div className="flex items-center gap-2">

<div className="flex bg-white rounded-lg border border-slate-200 overflow-hidden">

{(['month', 'week', 'today'] as const).map((v) => (

<button

key={v}

onClick={() => setViewMode(v)}

className={`px-3 py-2 text-sm font-medium transition-colors ${

viewMode === v ? 'bg-orange-600 text-white' : 'text-slate-600 hover:bg-slate-50'

}`}

>

{v === 'month' ? 'Месяц' : v === 'week' ? 'Неделя' : 'Сегодня'}

</button>

))}

</div>

<button

onClick={() => setShowCreate(true)}

className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700"

>

<Plus className="w-4 h-4" />

Событие

</button>

</div>

</div>


{/* Today Summary */}

{todaySummary && (

<div className="grid grid-cols-1 md:grid-cols-3 gap-4">

<div className="bg-white rounded-xl border border-slate-200 p-4">

<div className="flex items-center gap-2 mb-2">

<CalendarDays className="w-5 h-5 text-orange-600" />

<span className="font-medium text-slate-700">События сегодня</span>

</div>

<div className="text-2xl font-bold text-slate-900">{todaySummary.total_events}</div>

{todaySummary.events.length > 0 && (

<div className="mt-2 space-y-1">

{todaySummary.events.slice(0, 3).map(e => (

<div key={e.id} className="text-xs text-slate-600 flex items-center gap-1">

<Clock className="w-3 h-3" />

{new Date(e.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })} — {e.title}

</div>

))}

</div>

)}

</div>

<div className="bg-white rounded-xl border border-slate-200 p-4">

<div className="flex items-center gap-2 mb-2">

<CheckCircle2 className="w-5 h-5 text-amber-600" />

<span className="font-medium text-slate-700">Задачи на сегодня</span>

</div>

<div className="text-2xl font-bold text-slate-900">{todaySummary.total_tasks}</div>

{todaySummary.tasks_due.length > 0 && (

<div className="mt-2 space-y-1">

{todaySummary.tasks_due.slice(0, 3).map(t => (

<div key={t.id} className="text-xs text-slate-600">{t.title}</div>

))}

</div>

)}

</div>

<div className="bg-white rounded-xl border border-slate-200 p-4">

<div className="flex items-center gap-2 mb-2">

<AlertTriangle className="w-5 h-5 text-red-600" />

<span className="font-medium text-slate-700">Просрочено</span>

</div>

<div className="text-2xl font-bold text-red-600">{todaySummary.total_overdue}</div>

{todaySummary.overdue.length > 0 && (

<div className="mt-2 space-y-1">

{todaySummary.overdue.slice(0, 3).map(t => (

<div key={t.id} className="text-xs text-red-600">

{t.title} — {t.days_overdue} дн.

</div>

))}

</div>

)}

</div>

</div>

)}


{error && (

<div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm flex items-center gap-2">

<AlertTriangle className="w-4 h-4" />

{error}

<button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>

</div>

)}


{/* MONTH VIEW */}

{viewMode === 'month' && (

<div className="bg-white rounded-xl border border-slate-200 overflow-hidden">

{/* Month Header */}

<div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">

<button onClick={prevMonth} className="p-2 hover:bg-slate-100 rounded-lg">

<ChevronLeft className="w-5 h-5" />

</button>

<h2 className="text-lg font-semibold text-slate-900">

{monthNames[month - 1]} {year}

</h2>

<button onClick={nextMonth} className="p-2 hover:bg-slate-100 rounded-lg">

<ChevronRight className="w-5 h-5" />

</button>

</div>


{/* Week Days */}

<div className="grid grid-cols-7 border-b border-slate-200">

{weekDays.map(d => (

<div key={d} className="px-2 py-2 text-center text-xs font-medium text-slate-500">

{d}

</div>

))}

</div>


{/* Calendar Grid */}

{loading ? (

<div className="p-12 text-center">

<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600 mx-auto" />

</div>

) : (

<div className="grid grid-cols-7 auto-rows-fr">

{days.map((day) => {

const dayNum = parseInt(day.date.split('-')[2])

const isToday = day.date === new Date().toISOString().split('T')[0]

const hasEvents = day.events.length > 0

const hasTasks = day.tasks_due.length > 0

return (

<button

key={day.date}

onClick={() => setSelectedDay(day.date === selectedDay ? null : day.date)}

className={`min-h-[100px] p-2 border-r border-b border-slate-100 text-left hover:bg-slate-50 transition-colors ${

isToday ? 'bg-orange-50' : ''

} ${selectedDay === day.date ? 'ring-2 ring-orange-500 ring-inset' : ''}`}

>

<div className={`text-sm font-medium mb-1 ${isToday ? 'text-orange-600' : 'text-slate-700'}`}>

{dayNum}

</div>

<div className="space-y-1">

{day.events.slice(0, 2).map(e => (

<div

key={e.id}

className={`text-xs px-1.5 py-0.5 rounded text-white truncate ${

eventTypeColors[e.event_type] || 'bg-slate-500'

}`}

style={{ backgroundColor: e.color || undefined }}

>

{e.title}

</div>

))}

{day.events.length > 2 && (

<div className="text-xs text-slate-400">+{day.events.length - 2}</div>

)}

{day.tasks_due.slice(0, 2).map(t => (

<div key={t.id} className={`text-xs px-1.5 py-0.5 rounded ${priorityColors[t.priority]} text-slate-700 truncate`}>

{t.title}

</div>

))}

{day.tasks_due.length > 2 && (

<div className="text-xs text-slate-400">+{day.tasks_due.length - 2} задач</div>

)}

</div>

</button>

)

})}

</div>

)}

</div>

)}


{/* Selected Day Detail */}

{selectedDay && selectedDayData && (

<div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">

<div className="flex items-center justify-between">

<h3 className="font-semibold text-slate-900">

{new Date(selectedDay).toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })}

</h3>

<button onClick={() => setSelectedDay(null)} className="p-1 text-slate-400 hover:text-slate-600">

<X className="w-5 h-5" />

</button>

</div>


{selectedDayData.events.length > 0 && (

<div>

<h4 className="text-sm font-medium text-slate-600 mb-2">События</h4>

<div className="space-y-2">

{selectedDayData.events.map(e => (

<div key={e.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">

<div

className="w-3 h-3 rounded-full flex-shrink-0"

style={{ backgroundColor: e.color || '#3B82F6' }}

/>

<div className="flex-1">

<div className="font-medium text-sm text-slate-900">{e.title}</div>

<div className="text-xs text-slate-500 flex items-center gap-2 mt-0.5">

<Clock className="w-3 h-3" />

{e.all_day ? 'Весь день' : new Date(e.start_time).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}

{e.location && <><MapPin className="w-3 h-3 ml-1" /> {e.location}</>}

</div>

</div>

<span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-600">

{eventTypeLabels[e.event_type]}

</span>

</div>

))}

</div>

</div>

)}


{selectedDayData.tasks_due.length > 0 && (

<div>

<h4 className="text-sm font-medium text-slate-600 mb-2">Задачи</h4>

<div className="space-y-2">

{selectedDayData.tasks_due.map(t => (

<div key={t.id} className="flex items-center gap-3 p-3 bg-amber-50 rounded-lg">

<CheckCircle2 className="w-4 h-4 text-amber-600" />

<div className="flex-1">

<div className="font-medium text-sm text-slate-900">{t.title}</div>

</div>

<span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority]} text-slate-700`}>

{t.priority}

</span>

</div>

))}

</div>

</div>

)}


{selectedDayData.events.length === 0 && selectedDayData.tasks_due.length === 0 && (

<div className="text-center text-slate-400 py-4">Нет событий и задач</div>

)}

</div>

)}


{/* Create Event Modal */}

{showCreate && (

<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">

<div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">

<div className="flex items-center justify-between">

<h3 className="text-lg font-semibold">Новое событие</h3>

<button onClick={() => setShowCreate(false)}><X className="w-5 h-5 text-slate-400" /></button>

</div>

<div className="space-y-3">

<div>

<label className="text-sm text-slate-600">Название *</label>

<input

value={newEvent.title}

onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"

placeholder="Название события"

/>

</div>

<div>

<label className="text-sm text-slate-600">Тип</label>

<select

value={newEvent.event_type}

onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"

>

<option value="meeting">Встреча</option>

<option value="call">Звонок</option>

<option value="task">Задача</option>

<option value="deadline">Дедлайн</option>

<option value="reminder">Напоминание</option>

<option value="other">Другое</option>

</select>

</div>

<div className="grid grid-cols-2 gap-3">

<div>

<label className="text-sm text-slate-600">Начало *</label>

<input

type="datetime-local"

value={newEvent.start_time}

onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"

/>

</div>

<div>

<label className="text-sm text-slate-600">Окончание</label>

<input

type="datetime-local"

value={newEvent.end_time}

onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"

/>

</div>

</div>

<div>

<label className="text-sm text-slate-600">Место</label>

<input

value={newEvent.location}

onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"

placeholder="Адрес или ссылка"

/>

</div>

<div>

<label className="text-sm text-slate-600">Описание</label>

<textarea

value={newEvent.description}

onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}

className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm h-16 resize-none"

/>

</div>

<div className="flex items-center gap-2">

<input

type="checkbox"

id="all_day"

checked={newEvent.all_day}

onChange={(e) => setNewEvent({ ...newEvent, all_day: e.target.checked })}

className="rounded"

/>

<label htmlFor="all_day" className="text-sm text-slate-600">Весь день</label>

</div>

</div>

<div className="flex gap-3">

<button onClick={createEvent} className="flex-1 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700">

Создать

</button>

<button onClick={() => setShowCreate(false)} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">

Отмена

</button>

</div>

</div>

</div>

)}

</div>

)
}
