import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {
  CheckCircle2, Circle, Clock, AlertTriangle, AlertOctagon,
  Plus, Trash2, Edit3, Filter, Search, Calendar, ChevronDown,
  LayoutGrid, List, X, CheckCheck, ArrowUpDown
} from 'lucide-react'

interface Task {
  id: number
  title: string
  description: string | null
  status: string
  priority: string
  due_date: string | null
  completed_at: string | null
  client_id: number | null
  client_name: string | null
  deal_id: number | null
  deal_title: string | null
  created_at: string
  is_overdue: boolean
  days_until_due: number | null
}

interface TaskStats {
  total: number
  pending: number
  in_progress: number
  completed: number
  cancelled: number
  overdue: number
  due_today: number
  due_this_week: number
  by_priority: Record<string, number>
}

export default function Tasks() {
  const { user } = useAuthStore()
  const [tasks, setTasks] = useState<Task[]>([])
  const [stats, setStats] = useState<TaskStats | null>(null)
  const [viewMode, setViewMode] = useState<'list' | 'kanban'>('kanban')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed' | 'overdue'>('all')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [selectedTasks, setSelectedTasks] = useState<number[]>([])

  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: '',
    status: 'pending',
  })

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter !== 'all' && filter !== 'overdue') params.set('status', filter)
      if (filter === 'overdue') params.set('overdue', 'true')
      if (priorityFilter) params.set('priority', priorityFilter)
      if (search) params.set('search', search)

      const [tasksRes, statsRes] = await Promise.all([
        api.get(`/tasks/?${params}`),
        api.get('/tasks/stats'),
      ])
      setTasks(tasksRes.data)
      setStats(statsRes.data)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [filter, priorityFilter, search])

  const createTask = async () => {
    if (!newTask.title.trim()) return
    try {
      await api.post('/tasks/', {
        ...newTask,
        due_date: newTask.due_date ? new Date(newTask.due_date).toISOString() : null,
      })
      setShowCreate(false)
      setNewTask({ title: '', description: '', priority: 'medium', due_date: '', status: 'pending' })
      fetchTasks()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка создания')
    }
  }

  const updateTask = async () => {
    if (!editingTask) return
    try {
      await api.put(`/tasks/${editingTask.id}`, {
        title: editingTask.title,
        description: editingTask.description,
        priority: editingTask.priority,
        status: editingTask.status,
        due_date: editingTask.due_date,
      })
      setEditingTask(null)
      fetchTasks()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка обновления')
    }
  }

  const completeTask = async (id: number) => {
    try {
      await api.post(`/tasks/${id}/complete`)
      fetchTasks()
    } catch (e) {
      // ignore
    }
  }

  const deleteTask = async (id: number) => {
    if (!confirm('Удалить задачу?')) return
    try {
      await api.delete(`/tasks/${id}`)
      fetchTasks()
    } catch (e) {
      // ignore
    }
  }

  const bulkComplete = async () => {
    try {
      await api.post('/tasks/bulk/update', {
        task_ids: selectedTasks,
        status: 'completed',
      })
      setSelectedTasks([])
      fetchTasks()
    } catch (e) {
      // ignore
    }
  }

  const toggleSelect = (id: number) => {
    setSelectedTasks(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const priorityColors: Record<string, string> = {
    low: 'bg-slate-100 text-slate-600',
    medium: 'bg-blue-100 text-blue-700',
    high: 'bg-orange-100 text-orange-700',
    urgent: 'bg-red-100 text-red-700',
  }

  const priorityLabels: Record<string, string> = {
    low: 'Низкий',
    medium: 'Средний',
    high: 'Высокий',
    urgent: 'Срочный',
  }

  const statusLabels: Record<string, string> = {
    pending: 'В ожидании',
    in_progress: 'В работе',
    completed: 'Выполнено',
    cancelled: 'Отменено',
  }

  const statusIcons: Record<string, any> = {
    pending: Circle,
    in_progress: Clock,
    completed: CheckCircle2,
    cancelled: X,
  }

  const kanbanColumns = [
    { status: 'pending', title: 'В ожидании', color: 'bg-slate-100' },
    { status: 'in_progress', title: 'В работе', color: 'bg-blue-50' },
    { status: 'completed', title: 'Выполнено', color: 'bg-green-50' },
    { status: 'cancelled', title: 'Отменено', color: 'bg-red-50' },
  ]

  const filteredTasks = tasks

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Задачи</h1>
          <p className="text-slate-500 mt-1">Управление задачами и дедлайнами</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('kanban')}
            className={`p-2 rounded-lg ${viewMode === 'kanban' ? 'bg-blue-100 text-blue-700' : 'text-slate-400 hover:text-slate-600'}`}
          >
            <LayoutGrid className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-blue-100 text-blue-700' : 'text-slate-400 hover:text-slate-600'}`}
          >
            <List className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Новая задача
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { label: 'Всего', value: stats.total, color: 'text-slate-900' },
            { label: 'В ожидании', value: stats.pending, color: 'text-slate-600' },
            { label: 'В работе', value: stats.in_progress, color: 'text-blue-600' },
            { label: 'Выполнено', value: stats.completed, color: 'text-green-600' },
            { label: 'Просрочено', value: stats.overdue, color: 'text-red-600' },
            { label: 'На сегодня', value: stats.due_today, color: 'text-amber-600' },
            { label: 'На неделю', value: stats.due_this_week, color: 'text-purple-600' },
          ].map((s, i) => (
            <div key={i} className="bg-white rounded-lg border border-slate-200 p-3 text-center">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex bg-white rounded-lg border border-slate-200 overflow-hidden">
          {(['all', 'pending', 'in_progress', 'completed', 'overdue'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                filter === f ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              {f === 'all' ? 'Все' : f === 'in_progress' ? 'В работе' : f === 'overdue' ? 'Просрочено' : statusLabels[f]}
            </button>
          ))}
        </div>
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
        >
          <option value="">Все приоритеты</option>
          <option value="low">Низкий</option>
          <option value="medium">Средний</option>
          <option value="high">Высокий</option>
          <option value="urgent">Срочный</option>
        </select>
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Поиск задач..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
        {selectedTasks.length > 0 && (
          <button
            onClick={bulkComplete}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
          >
            <CheckCheck className="w-4 h-4" />
            Завершить ({selectedTasks.length})
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error}
          <button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* KANBAN VIEW */}
      {viewMode === 'kanban' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kanbanColumns.map((col) => {
            const colTasks = filteredTasks.filter(t => t.status === col.status)
            return (
              <div key={col.status} className={`${col.color} rounded-xl border border-slate-200 p-3`}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-sm text-slate-700">{col.title}</h3>
                  <span className="bg-white text-slate-500 text-xs px-2 py-0.5 rounded-full font-medium">
                    {colTasks.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {colTasks.map((task) => (
                    <div
                      key={task.id}
                      className={`bg-white rounded-lg p-3 border border-slate-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${
                        task.is_overdue ? 'border-red-300' : ''
                      }`}
                      onClick={() => setEditingTask(task)}
                    >
                      <div className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={selectedTasks.includes(task.id)}
                          onClick={(e) => e.stopPropagation()}
                          onChange={() => toggleSelect(task.id)}
                          className="mt-1"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm text-slate-900 truncate">{task.title}</div>
                          {task.description && (
                            <div className="text-xs text-slate-500 mt-1 line-clamp-2">{task.description}</div>
                          )}
                          <div className="flex items-center gap-2 mt-2 flex-wrap">
                            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${priorityColors[task.priority]}`}>
                              {priorityLabels[task.priority]}
                            </span>
                            {task.due_date && (
                              <span className={`text-xs flex items-center gap-1 ${
                                task.is_overdue ? 'text-red-600' : 'text-slate-400'
                              }`}>
                                <Calendar className="w-3 h-3" />
                                {task.is_overdue
                                  ? `Просрочено ${Math.abs(task.days_until_due || 0)} дн`
                                  : task.days_until_due === 0
                                  ? 'Сегодня'
                                  : `Через ${task.days_until_due} дн`
                                }
                              </span>
                            )}
                          </div>
                          {task.client_name && (
                            <div className="text-xs text-slate-400 mt-1">{task.client_name}</div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 mt-2 pt-2 border-t border-slate-100">
                        {task.status !== 'completed' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); completeTask(task.id) }}
                            className="p-1 text-green-500 hover:bg-green-50 rounded"
                            title="Завершить"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={(e) => { e.stopPropagation(); setEditingTask(task) }}
                          className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Редактировать"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteTask(task.id) }}
                          className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Удалить"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* LIST VIEW */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>Задач не найдено</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 w-8"></th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Задача</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Приоритет</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Статус</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Дедлайн</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Действия</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredTasks.map((task) => {
                  const StatusIcon = statusIcons[task.status]
                  return (
                    <tr key={task.id} className={`hover:bg-slate-50 ${task.is_overdue ? 'bg-red-50/50' : ''}`}>
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedTasks.includes(task.id)}
                          onChange={() => toggleSelect(task.id)}
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{task.title}</div>
                        {task.description && (
                          <div className="text-xs text-slate-500 mt-0.5">{task.description}</div>
                        )}
                        {task.client_name && (
                          <div className="text-xs text-slate-400 mt-0.5">{task.client_name}</div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${priorityColors[task.priority]}`}>
                          {priorityLabels[task.priority]}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="flex items-center gap-1 text-xs text-slate-600">
                          <StatusIcon className="w-3.5 h-3.5" />
                          {statusLabels[task.status]}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {task.due_date ? (
                          <span className={`text-xs ${task.is_overdue ? 'text-red-600 font-medium' : 'text-slate-500'}`}>
                            {new Date(task.due_date).toLocaleDateString('ru-RU')}
                            {task.is_overdue && ' (просрочено)'}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {task.status !== 'completed' && (
                            <button onClick={() => completeTask(task.id)} className="p-1 text-green-500 hover:bg-green-50 rounded">
                              <CheckCircle2 className="w-4 h-4" />
                            </button>
                          )}
                          <button onClick={() => setEditingTask(task)} className="p-1 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded">
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button onClick={() => deleteTask(task.id)} className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Новая задача</h3>
              <button onClick={() => setShowCreate(false)}><X className="w-5 h-5 text-slate-400" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-600">Название *</label>
                <input
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="Название задачи"
                />
              </div>
              <div>
                <label className="text-sm text-slate-600">Описание</label>
                <textarea
                  value={newTask.description}
                  onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm h-20 resize-none"
                  placeholder="Описание..."
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-slate-600">Приоритет</label>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-600">Дедлайн</label>
                  <input
                    type="datetime-local"
                    value={newTask.due_date}
                    onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={createTask} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                Создать
              </button>
              <button onClick={() => setShowCreate(false)} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Редактировать задачу</h3>
              <button onClick={() => setEditingTask(null)}><X className="w-5 h-5 text-slate-400" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-600">Название</label>
                <input
                  value={editingTask.title}
                  onChange={(e) => setEditingTask({ ...editingTask, title: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm text-slate-600">Описание</label>
                <textarea
                  value={editingTask.description || ''}
                  onChange={(e) => setEditingTask({ ...editingTask, description: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm h-20 resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm text-slate-600">Статус</label>
                  <select
                    value={editingTask.status}
                    onChange={(e) => setEditingTask({ ...editingTask, status: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="pending">В ожидании</option>
                    <option value="in_progress">В работе</option>
                    <option value="completed">Выполнено</option>
                    <option value="cancelled">Отменено</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-600">Приоритет</label>
                  <select
                    value={editingTask.priority}
                    onChange={(e) => setEditingTask({ ...editingTask, priority: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-600">Дедлайн</label>
                <input
                  type="datetime-local"
                  value={editingTask.due_date ? editingTask.due_date.slice(0, 16) : ''}
                  onChange={(e) => setEditingTask({ ...editingTask, due_date: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={updateTask} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                Сохранить
              </button>
              <button onClick={() => setEditingTask(null)} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
