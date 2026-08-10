import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {
  Users, Shield, BarChart3, Search, Filter,
  Lock, Unlock, Trash2, Eye, Edit3, Crown,
  ChevronLeft, ChevronRight, X, CheckCircle,
  AlertTriangle, Clock, Mail, Phone, Calendar
} from 'lucide-react'

interface UserAdmin {
  id: number
  email: string
  full_name: string | null
  phone: string | null
  inn: string | null
  is_active: boolean
  is_verified: boolean
  is_admin: boolean
  is_moderator: boolean
  subscription_tier: string
  subscription_expires: string | null
  points: number
  level: string
  failed_login_attempts: number
  locked_until: string | null
  last_login_at: string | null
  created_at: string
  role: string
}

interface PlatformStats {
  total_users: number
  active_users_30d: number
  new_users_today: number
  new_users_week: number
  new_users_month: number
  total_revenue: number
  paid_invoices_count: number
  subscriptions_by_tier: Record<string, { count: number; percentage: number }>
  avg_invoices_per_user: number
  top_actions: { action: string; count: number }[]
  users_by_month: { month: string; count: number }[]
}

export default function AdminPanel() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'users' | 'stats' | 'audit'>('users')
  const [users, setUsers] = useState<UserAdmin[]>([])
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState('')
  const [editUser, setEditUser] = useState<UserAdmin | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showBlockModal, setShowBlockModal] = useState(false)
  const [blockReason, setBlockReason] = useState('')
  const [blockDuration, setBlockDuration] = useState('')
  const [blockTarget, setBlockTarget] = useState<UserAdmin | null>(null)
  const [message, setMessage] = useState('')

  // Redirect non-admins
  useEffect(() => {
    if (user && !user.is_admin) {
      navigate('/dashboard')
    }
  }, [user, navigate])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('page', String(page))
      params.set('per_page', '20')
      if (search) params.set('search', search)
      if (tierFilter) params.set('tier', tierFilter)

      const res = await api.get(`/admin/users?${params}`)
      setUsers(res.data.users)
      setTotalPages(res.data.pagination.total_pages)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка загрузки пользователей')
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    try {
      const res = await api.get('/admin/stats')
      setStats(res.data)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка загрузки статистики')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'users') fetchUsers()
    if (activeTab === 'stats') fetchStats()
  }, [activeTab, page, search, tierFilter])

  const handleBlock = async () => {
    if (!blockTarget) return
    try {
      await api.post(`/admin/users/${blockTarget.id}/block`, {
        action: 'block',
        reason: blockReason,
        duration_hours: blockDuration ? parseInt(blockDuration) : null,
      })
      setMessage(`Пользователь ${blockTarget.email} заблокирован`)
      setShowBlockModal(false)
      setBlockReason('')
      setBlockDuration('')
      setBlockTarget(null)
      fetchUsers()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка блокировки')
    }
  }

  const handleUnblock = async (u: UserAdmin) => {
    try {
      await api.post(`/admin/users/${u.id}/unblock`)
      setMessage(`Пользователь ${u.email} разблокирован`)
      fetchUsers()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка разблокировки')
    }
  }

  const handleDelete = async (u: UserAdmin) => {
    if (!confirm(`Удалить пользователя ${u.email}? Это необратимо.`)) return
    try {
      await api.delete(`/admin/users/${u.id}`)
      setMessage(`Пользователь ${u.email} удалён`)
      fetchUsers()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка удаления')
    }
  }

  const handleUpdateUser = async () => {
    if (!editUser) return
    try {
      await api.put(`/admin/users/${editUser.id}`, {
        full_name: editUser.full_name,
        phone: editUser.phone,
        is_active: editUser.is_active,
        is_verified: editUser.is_verified,
        is_admin: editUser.is_admin,
        is_moderator: editUser.is_moderator,
        subscription_tier: editUser.subscription_tier,
      })
      setMessage('Пользователь обновлён')
      setShowEditModal(false)
      setEditUser(null)
      fetchUsers()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка обновления')
    }
  }

  const tierColors: Record<string, string> = {
    free: 'bg-slate-100 text-slate-700',
    pro: 'bg-blue-100 text-blue-700',
    business: 'bg-purple-100 text-purple-700',
    enterprise: 'bg-amber-100 text-amber-700',
  }

  const tierLabels: Record<string, string> = {
    free: 'Бесплатный',
    pro: 'Профессиональный',
    business: 'Бизнес',
    enterprise: 'Корпоративный',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-7 h-7 text-blue-600" />
            Админ-панель
          </h1>
          <p className="text-slate-500 mt-1">Управление пользователями, модерация и статистика платформы</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'users' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            <Users className="w-4 h-4" />
            Пользователи
          </button>
          <button
            onClick={() => setActiveTab('stats')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'stats' ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Статистика
          </button>
          <button
            onClick={() => navigate('/admin/audit-logs')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <Eye className="w-4 h-4" />
            Аудит
          </button>
        </div>
      </div>

      {/* Messages */}
      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2 text-green-700">
          <CheckCircle className="w-5 h-5" />
          {message}
          <button onClick={() => setMessage('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          {error}
          <button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* USERS TAB */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* Filters */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 flex flex-wrap gap-3">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Поиск по email, имени, телефону, ИНН..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <select
              value={tierFilter}
              onChange={(e) => { setTierFilter(e.target.value); setPage(1) }}
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все тарифы</option>
              <option value="free">Бесплатный</option>
              <option value="pro">Профессиональный</option>
              <option value="business">Бизнес</option>
              <option value="enterprise">Корпоративный</option>
            </select>
            <button
              onClick={fetchUsers}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 transition-colors"
            >
              Обновить
            </button>
          </div>

          {/* Users Table */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-slate-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3" />
                Загрузка...
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Пользователь</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Тариф</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Статус</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Роль</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Регистрация</th>
                        <th className="px-4 py-3 text-left font-medium text-slate-600">Действия</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {users.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                                u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                              }`}>
                                {u.full_name?.[0]?.toUpperCase() || u.email[0].toUpperCase()}
                              </div>
                              <div>
                                <div className="font-medium text-slate-900">{u.full_name || '—'}</div>
                                <div className="text-slate-500 text-xs flex items-center gap-1">
                                  <Mail className="w-3 h-3" />
                                  {u.email}
                                </div>
                                {u.phone && (
                                  <div className="text-slate-400 text-xs flex items-center gap-1">
                                    <Phone className="w-3 h-3" />
                                    {u.phone}
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                              tierColors[u.subscription_tier] || tierColors.free
                            }`}>
                              <Crown className="w-3 h-3" />
                              {tierLabels[u.subscription_tier] || u.subscription_tier}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-col gap-1">
                              <span className={`inline-flex items-center gap-1 text-xs ${
                                u.is_active ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {u.is_active ? (
                                  <><CheckCircle className="w-3 h-3" /> Активен</>
                                ) : (
                                  <><X className="w-3 h-3" /> Заблокирован</>
                                )}
                              </span>
                              {u.is_verified && (
                                <span className="text-xs text-blue-600">Подтверждён</span>
                              )}
                              {u.locked_until && (
                                <span className="text-xs text-amber-600 flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  До {new Date(u.locked_until).toLocaleDateString('ru-RU')}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                              u.is_admin ? 'bg-red-100 text-red-700' :
                              u.is_moderator ? 'bg-orange-100 text-orange-700' :
                              'bg-slate-100 text-slate-600'
                            }`}>
                              {u.is_admin ? 'Админ' : u.is_moderator ? 'Модератор' : 'Пользователь'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-500 text-xs">
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(u.created_at).toLocaleDateString('ru-RU')}
                            </div>
                            {u.last_login_at && (
                              <div className="text-slate-400 mt-1">
                                Вход: {new Date(u.last_login_at).toLocaleDateString('ru-RU')}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1">
                              <button
                                onClick={() => { setEditUser(u); setShowEditModal(true) }}
                                className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                                title="Редактировать"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              {u.is_active ? (
                                <button
                                  onClick={() => { setBlockTarget(u); setShowBlockModal(true) }}
                                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                  title="Заблокировать"
                                >
                                  <Lock className="w-4 h-4" />
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleUnblock(u)}
                                  className="p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                  title="Разблокировать"
                                >
                                  <Unlock className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => navigate(`/admin/audit-logs?user_id=${u.id}`)}
                                className="p-1.5 text-slate-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                                title="Аудит-логи"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(u)}
                                className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                title="Удалить"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
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
        </div>
      )}

      {/* STATS TAB */}
      {activeTab === 'stats' && stats && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-slate-500 text-sm mb-1">Всего пользователей</div>
              <div className="text-3xl font-bold text-slate-900">{stats.total_users.toLocaleString('ru-RU')}</div>
              <div className="text-green-600 text-xs mt-2 flex items-center gap-1">
                <Users className="w-3 h-3" />
                {stats.active_users_30d} активных за 30 дней
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-slate-500 text-sm mb-1">Новые сегодня</div>
              <div className="text-3xl font-bold text-slate-900">{stats.new_users_today}</div>
              <div className="text-slate-400 text-xs mt-2">
                {stats.new_users_week} за неделю · {stats.new_users_month} за месяц
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-slate-500 text-sm mb-1">Общая выручка</div>
              <div className="text-3xl font-bold text-slate-900">
                {stats.total_revenue.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' })}
              </div>
              <div className="text-slate-400 text-xs mt-2">
                {stats.paid_invoices_count} оплаченных счетов
              </div>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="text-slate-500 text-sm mb-1">Счетов на пользователя</div>
              <div className="text-3xl font-bold text-slate-900">{stats.avg_invoices_per_user}</div>
              <div className="text-slate-400 text-xs mt-2">Среднее значение</div>
            </div>
          </div>

          {/* Subscriptions */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Crown className="w-5 h-5 text-amber-500" />
              Распределение по тарифам
            </h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(stats.subscriptions_by_tier).map(([tier, data]) => (
                <div key={tier} className={`rounded-lg p-4 ${tierColors[tier] || tierColors.free}`}>
                  <div className="text-sm font-medium opacity-80">{tierLabels[tier] || tier}</div>
                  <div className="text-2xl font-bold mt-1">{data.count}</div>
                  <div className="text-xs opacity-70 mt-1">{data.percentage}% от всех</div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Топ действий</h3>
              <div className="space-y-2">
                {stats.top_actions.map((a, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                    <span className="text-sm text-slate-700">{a.action}</span>
                    <span className="text-sm font-medium text-slate-900">{a.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Регистрации по месяцам</h3>
              <div className="space-y-2">
                {stats.users_by_month.map((m, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                    <span className="text-sm text-slate-700">{m.month}</span>
                    <span className="text-sm font-medium text-slate-900">{m.count} пользователей</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Редактировать пользователя</h3>
              <button onClick={() => setShowEditModal(false)}><X className="w-5 h-5 text-slate-400" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-600">Имя</label>
                <input
                  value={editUser.full_name || ''}
                  onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm text-slate-600">Телефон</label>
                <input
                  value={editUser.phone || ''}
                  onChange={(e) => setEditUser({ ...editUser, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="text-sm text-slate-600">Тариф</label>
                <select
                  value={editUser.subscription_tier}
                  onChange={(e) => setEditUser({ ...editUser, subscription_tier: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="free">Бесплатный</option>
                  <option value="pro">Профессиональный</option>
                  <option value="business">Бизнес</option>
                  <option value="enterprise">Корпоративный</option>
                </select>
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editUser.is_active}
                    onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })}
                  />
                  Активен
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editUser.is_verified}
                    onChange={(e) => setEditUser({ ...editUser, is_verified: e.target.checked })}
                  />
                  Подтверждён
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editUser.is_admin}
                    onChange={(e) => setEditUser({ ...editUser, is_admin: e.target.checked })}
                  />
                  Админ
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={editUser.is_moderator}
                    onChange={(e) => setEditUser({ ...editUser, is_moderator: e.target.checked })}
                  />
                  Модератор
                </label>
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleUpdateUser}
                className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
              >
                Сохранить
              </button>
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Block Modal */}
      {showBlockModal && blockTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-3 text-red-600">
              <Lock className="w-6 h-6" />
              <h3 className="text-lg font-semibold">Блокировка пользователя</h3>
            </div>
            <p className="text-slate-600 text-sm">
              Вы собираетесь заблокировать <strong>{blockTarget.email}</strong>
            </p>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-600">Причина</label>
                <textarea
                  value={blockReason}
                  onChange={(e) => setBlockReason(e.target.value)}
                  placeholder="Укажите причину блокировки..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm h-20 resize-none"
                />
              </div>
              <div>
                <label className="text-sm text-slate-600">Длительность (часов, пусто = навсегда)</label>
                <input
                  type="number"
                  value={blockDuration}
                  onChange={(e) => setBlockDuration(e.target.value)}
                  placeholder="Навсегда"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleBlock}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
              >
                Заблокировать
              </button>
              <button
                onClick={() => setShowBlockModal(false)}
                className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
