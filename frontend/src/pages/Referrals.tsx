import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {
  Users, Gift, Trophy, Crown, Copy, CheckCircle,
  Link2, ChevronRight, Star, TrendingUp, Share2,
  AlertTriangle, X, UserPlus
} from 'lucide-react'

interface ReferralStats {
  referral_code: string
  referral_link: string
  total_referrals: number
  active_referrals: number
  paid_referrals: number
  total_earnings: number
  pending_earnings: number
  level: string
  level_bonus_pct: number
  next_level: string | null
  next_level_min: number | null
}

interface Referral {
  id: number
  referred_email: string
  referred_name: string | null
  status: string
  reward_amount: number
  reward_paid: boolean
  created_at: string
  converted_at: string | null
}

interface LeaderboardEntry {
  rank: number
  name: string
  referrals: number
  earnings: number
  points: number
  level: string
}

interface LevelInfo {
  name: string
  min: number
  bonus_pct: number
}

export default function Referrals() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState<ReferralStats | null>(null)
  const [referrals, setReferrals] = useState<Referral[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [levels, setLevels] = useState<LevelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [applyCode, setApplyCode] = useState('')
  const [applyMessage, setApplyMessage] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsRes, refsRes, lbRes, levelsRes] = await Promise.all([
        api.get('/referrals/me'),
        api.get('/referrals/my-referrals'),
        api.get('/referrals/leaderboard'),
        api.get('/referrals/levels'),
      ])
      setStats(statsRes.data)
      setReferrals(refsRes.data)
      setLeaderboard(lbRes.data)
      setLevels(levelsRes.data.levels)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const copyLink = () => {
    if (!stats) return
    navigator.clipboard.writeText(stats.referral_link)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleApplyCode = async () => {
    if (!applyCode.trim()) return
    try {
      const res = await api.post('/referrals/apply', { code: applyCode.trim() })
      setApplyMessage(`Код применён! Реферер: ${res.data.referrer}`)
      setApplyCode('')
      fetchData()
    } catch (e: any) {
      setApplyMessage(e.response?.data?.message || 'Ошибка применения кода')
    }
  }

  const shareVia = (platform: string) => {
    if (!stats) return
    const text = `Присоединяйся к Миру Самозанятых! Моя реферальная ссылка: ${stats.referral_link}`
    const urls: Record<string, string> = {
      telegram: `https://t.me/share/url?url=${encodeURIComponent(stats.referral_link)}&text=${encodeURIComponent(text)}`,
      whatsapp: `https://wa.me/?text=${encodeURIComponent(text)}`,
      vk: `https://vk.com/share.php?url=${encodeURIComponent(stats.referral_link)}`,
    }
    if (urls[platform]) window.open(urls[platform], '_blank')
  }

  const statusColors: Record<string, string> = {
    registered: 'bg-blue-100 text-blue-700',
    active: 'bg-green-100 text-green-700',
    paid: 'bg-amber-100 text-amber-700',
  }

  const statusLabels: Record<string, string> = {
    registered: 'Зарегистрирован',
    active: 'Активен',
    paid: 'Оплатил',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Gift className="w-7 h-7 text-amber-500" />
          Реферальная программа
        </h1>
        <p className="text-slate-500 mt-1">Приглашайте друзей и получайте бонусы</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          {error}
          <button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {applyMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2 text-green-700">
          <CheckCircle className="w-5 h-5" />
          {applyMessage}
          <button onClick={() => setApplyMessage('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="text-slate-500 text-sm mb-1">Всего приглашено</div>
            <div className="text-3xl font-bold text-slate-900">{stats.total_referrals}</div>
            <div className="text-blue-600 text-xs mt-2 flex items-center gap-1">
              <Users className="w-3 h-3" />
              {stats.active_referrals} активных
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="text-slate-500 text-sm mb-1">Заработано</div>
            <div className="text-3xl font-bold text-green-600">
              {stats.total_earnings.toLocaleString('ru-RU')} ₽
            </div>
            <div className="text-amber-600 text-xs mt-2">
              {stats.pending_earnings.toLocaleString('ru-RU')} ₽ в ожидании
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="text-slate-500 text-sm mb-1">Уровень</div>
            <div className="text-3xl font-bold text-purple-600">{stats.level}</div>
            <div className="text-purple-600 text-xs mt-2">
              Бонус +{stats.level_bonus_pct}%
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="text-slate-500 text-sm mb-1">Следующий уровень</div>
            <div className="text-2xl font-bold text-slate-900">
              {stats.next_level || 'Максимум!'}
            </div>
            {stats.next_level_min && (
              <div className="text-slate-400 text-xs mt-2">
                Нужно ещё {stats.next_level_min - stats.total_referrals} приглашений
              </div>
            )}
          </div>
        </div>
      )}

      {/* Referral Link & Apply Code */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <Link2 className="w-5 h-5 text-blue-600" />
            Ваша реферальная ссылка
          </h3>
          {stats && (
            <>
              <div className="flex gap-2">
                <input
                  readOnly
                  value={stats.referral_link}
                  className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600"
                />
                <button
                  onClick={copyLink}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 flex items-center gap-2"
                >
                  {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Скопировано' : 'Копировать'}
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => shareVia('telegram')}
                  className="flex-1 py-2 bg-sky-50 text-sky-700 rounded-lg text-sm hover:bg-sky-100 flex items-center justify-center gap-2"
                >
                  <Share2 className="w-4 h-4" />
                  Telegram
                </button>
                <button
                  onClick={() => shareVia('whatsapp')}
                  className="flex-1 py-2 bg-green-50 text-green-700 rounded-lg text-sm hover:bg-green-100 flex items-center justify-center gap-2"
                >
                  <Share2 className="w-4 h-4" />
                  WhatsApp
                </button>
                <button
                  onClick={() => shareVia('vk')}
                  className="flex-1 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm hover:bg-blue-100 flex items-center justify-center gap-2"
                >
                  <Share2 className="w-4 h-4" />
                  VK
                </button>
              </div>
            </>
          )}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-green-600" />
            Применить реферальный код
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Введите код друга..."
              value={applyCode}
              onChange={(e) => setApplyCode(e.target.value)}
              className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleApplyCode}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700"
            >
              Применить
            </button>
          </div>
          <p className="text-xs text-slate-400">
            Введите код друга, который пригласил вас, и получите бонус при регистрации.
          </p>
        </div>
      </div>

      {/* My Referrals */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            Мои рефералы
          </h3>
        </div>
        {referrals.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <Gift className="w-12 h-12 mx-auto mb-3 text-slate-300" />
            <p>У вас пока нет рефералов</p>
            <p className="text-sm text-slate-400 mt-1">Поделитесь ссылкой с друзьями!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Статус</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Награда</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Дата</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {referrals.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{r.referred_name || '—'}</div>
                      <div className="text-slate-500 text-xs">{r.referred_email}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                        statusColors[r.status] || 'bg-slate-100 text-slate-700'
                      }`}>
                        {statusLabels[r.status] || r.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-900">{r.reward_amount} ₽</div>
                      <div className="text-xs text-slate-400">
                        {r.reward_paid ? 'Выплачено' : 'В ожидании'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {new Date(r.created_at).toLocaleDateString('ru-RU')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Levels */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          Уровни реферальной программы
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {levels.map((level, i) => {
            const isCurrent = stats?.level === level.name
            return (
              <div
                key={i}
                className={`rounded-lg p-4 border-2 transition-all ${
                  isCurrent
                    ? 'border-purple-500 bg-purple-50'
                    : 'border-slate-100 bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {i === 0 && <Star className="w-4 h-4 text-slate-400" />}
                  {i === 1 && <TrendingUp className="w-4 h-4 text-blue-400" />}
                  {i === 2 && <Crown className="w-4 h-4 text-amber-400" />}
                  {i === 3 && <Trophy className="w-4 h-4 text-purple-400" />}
                  <span className={`font-semibold text-sm ${isCurrent ? 'text-purple-700' : 'text-slate-700'}`}>
                    {level.name}
                  </span>
                </div>
                <div className="text-2xl font-bold text-slate-900">{level.bonus_pct}%</div>
                <div className="text-xs text-slate-500 mt-1">от {level.min} рефералов</div>
                {isCurrent && (
                  <div className="mt-2 text-xs font-medium text-purple-600">Ваш уровень</div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Leaderboard */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            Топ рефереров
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">#</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Пользователь</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Рефералы</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Заработок</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Уровень</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {leaderboard.map((entry) => (
                <tr key={entry.rank} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                      entry.rank === 1 ? 'bg-amber-100 text-amber-700' :
                      entry.rank === 2 ? 'bg-slate-200 text-slate-700' :
                      entry.rank === 3 ? 'bg-orange-100 text-orange-700' :
                      'bg-slate-100 text-slate-500'
                    }`}>
                      {entry.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900">{entry.name}</td>
                  <td className="px-4 py-3 text-slate-700">{entry.referrals}</td>
                  <td className="px-4 py-3 font-medium text-green-600">
                    {entry.earnings.toLocaleString('ru-RU')} ₽
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                      {entry.level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
