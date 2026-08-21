import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useState, useEffect } from 'react'
import { LayoutDashboard, FileText, Users, Handshake, Settings, LogOut, Menu, X, Bell, Calculator, Calendar, BookOpen, Sparkles, UserCircle, Shield, Mail, BarChart3, Receipt, Download, MessageCircle } from 'lucide-react'
import SvetlanaAvatar from './SvetlanaAvatar'
import ThemeToggle from './ThemeToggle'
import { API_BASE_URL } from '../api/client'

const navItems = [
  { to: '/dashboard', label: 'Обзор', icon: LayoutDashboard },
  { to: '/invoices', label: 'Счета', icon: FileText },
  { to: '/clients', label: 'Клиенты', icon: Users },
  { to: '/deals', label: 'Сделки', icon: Handshake },
  { to: '/tasks', label: 'Задачи', icon: Sparkles },
  { to: '/calendar', label: 'Календарь', icon: Calendar },
  { to: '/accounting', label: 'Финансы', icon: Calculator },
  { to: '/receipt-check', label: 'Чеки ФНС', icon: Receipt },
  { to: '/email-campaigns', label: 'Рассылки', icon: Mail },
  { to: '/integrations', label: 'Интеграции', icon: BarChart3 },
  { to: '/docs', label: 'Документы', icon: BookOpen },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const logoUrl = `${API_BASE_URL}/static/logo-mir-samozanyatykh.png`

  useEffect(() => {
    const fetchUnread = async () => {
      try {
        const { default: apiClient } = await import('../api/client')
        const res = await apiClient.get('/api/notifications/unread-count')
        setUnreadCount(res.data.unread_count || 0)
      } catch {}
    }
    void fetchUnread()
    const interval = setInterval(fetchUnread, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleLogout = async () => {
    try {
      const { default: apiClient } = await import('../api/client')
      await apiClient.post('/api/auth/logout')
    } catch {} finally {
      logout()
      navigate('/login')
    }
  }

  const isAdmin = user?.is_admin || user?.is_moderator

  return (
    <div className="app-shell min-h-screen text-slate-900">
      {sidebarOpen && <div className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm lg:hidden" onClick={() => setSidebarOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-[270px] flex-col border-r border-slate-200/80 bg-white/95 backdrop-blur-xl transition-transform lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="px-5 pb-4 pt-5">
          <Link to="/" aria-label="Мир Самозанятых — на главную" className="brand-lockup flex items-center gap-3">
            <img src={logoUrl} alt="Мир Самозанятых" className="h-12 w-12 shrink-0 object-contain" />
            <div><div className="text-[17px] font-black tracking-tight">Мир</div><div className="text-[17px] font-black leading-4 tracking-tight">Самозанятых</div><div className="mt-1 text-[10px] text-slate-400">рабочее пространство</div></div>
          </Link>
          <button onClick={() => setSidebarOpen(false)} className="absolute right-3 top-3 rounded-lg p-2 hover:bg-slate-100 lg:hidden" aria-label="Закрыть меню"><X className="h-5 w-5" /></button>
        </div>
        <div className="px-4">
          <Link to="/svetlana" className="svetlana-nav-card flex items-center gap-3 rounded-2xl p-3 transition hover:-translate-y-0.5">
            <SvetlanaAvatar size="sm" /><div className="min-w-0 flex-1"><div className="text-sm font-bold">Светлана</div><div className="text-[11px] text-slate-500">ваш ИИ-ассистент</div></div><MessageCircle className="h-4 w-4 shrink-0 text-orange-500" />
          </Link>
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-5" aria-label="Рабочее пространство">
          <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">Рабочее пространство</div>
          {navItems.map(item => {
            const Icon = item.icon
            const active = location.pathname === item.to || location.pathname.startsWith(`${item.to}/`)
            return <Link key={item.to} to={item.to} onClick={() => setSidebarOpen(false)} className={`nav-item flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? 'nav-item-active' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'}`}><Icon className="h-4 w-4 shrink-0" strokeWidth={1.9}/><span>{item.label}</span></Link>
          })}
          <div className="px-3 pb-2 pt-5 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">Сервис</div>
          <Link to="/downloads" onClick={() => setSidebarOpen(false)} className="download-nav flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-bold"><Download className="h-4 w-4 shrink-0"/>Скачать приложение</Link>
          {isAdmin && <><Link to="/admin" className="mt-1 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"><Shield className="h-4 w-4 shrink-0"/>Администрирование</Link><Link to="/admin/audit-logs" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-600 hover:bg-slate-50"><BarChart3 className="h-4 w-4 shrink-0"/>Аудит</Link></>}
        </nav>
        <div className="border-t border-slate-100 p-4">
          <Link to="/profile" className="mb-2 flex items-center gap-3 rounded-xl p-2 hover:bg-slate-50"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-sm font-bold text-orange-700">{user?.full_name?.[0] || user?.email?.[0] || 'U'}</div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{user?.full_name || user?.email}</p><p className="text-[11px] text-slate-400">{user?.tier || 'free'}</p></div><Settings className="h-4 w-4 shrink-0 text-slate-400"/></Link>
          <button onClick={handleLogout} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-50 hover:text-slate-900"><LogOut className="h-4 w-4 shrink-0"/>Выйти</button>
        </div>
      </aside>
      <div className="min-h-screen lg:pl-[270px]">
        <header className="topbar sticky top-0 z-30 flex h-[72px] items-center justify-between border-b border-slate-200/80 px-4 sm:px-6">
          <button onClick={() => setSidebarOpen(true)} className="rounded-xl p-2 hover:bg-slate-100 lg:hidden" aria-label="Открыть меню"><Menu className="h-5 w-5"/></button>
          <div className="hidden items-center gap-3 lg:flex"><span className="text-sm font-semibold text-slate-900">{location.pathname === '/dashboard' ? 'Ваш рабочий день' : 'Мир Самозанятых'}</span><span className="h-1 w-1 rounded-full bg-orange-400"/><span className="text-xs text-slate-400">всё под контролем</span></div>
          <div className="ml-auto flex items-center gap-2"><ThemeToggle/><Link to="/notifications" aria-label="Уведомления" className="relative rounded-xl p-2.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"><Bell className="h-5 w-5"/>{unreadCount > 0 && <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-bold text-white">{unreadCount > 9 ? '9+' : unreadCount}</span>}</Link><Link to="/profile" aria-label="Профиль" className="rounded-xl p-2.5 text-slate-500 hover:bg-slate-100 lg:hidden"><UserCircle className="h-5 w-5"/></Link></div>
        </header>
        <main className="min-h-[calc(100vh-128px)] p-4 sm:p-6 lg:p-8"><Outlet /></main>
        <footer className="border-t border-slate-200/70 bg-white/70 px-4 py-4 text-center text-xs text-slate-400">Мир Самозанятых · Светлана рядом · безопасное рабочее пространство</footer>
      </div>
    </div>
  )
}
