import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { LayoutDashboard, Package, FileText, Users, Handshake, FileSignature, UserCircle, Mic, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/products', label: 'Produkty', icon: Package },
  { path: '/invoices', label: 'Scheta', icon: FileText },
  { path: '/clients', label: 'Klienty', icon: Users },
  { path: '/deals', label: 'Sdelki', icon: Handshake },
  { path: '/contracts', label: 'Dogovory', icon: FileSignature },
  { path: '/svetlana', label: 'Svetlana', icon: Mic },
  { path: '/profile', label: 'Profil', icon: UserCircle },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">MS</span>
              </div>
              <span className="font-semibold text-slate-800 hidden sm:block">Mir Samozanyatykh</span>
            </Link>
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <span className="text-sm text-slate-600 hidden sm:block">{user.email}</span>
                  <button onClick={logout} className="flex items-center gap-1 text-sm text-red-600 hover:text-red-700">
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Vyyti</span>
                  </button>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Link to="/login" className="text-sm text-slate-600 hover:text-slate-800">Vkhod</Link>
                  <Link to="/register" className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700">Registratsiya</Link>
                </div>
              )}
              <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="sm:hidden p-2 text-slate-600">
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>
      <div className="max-w-7xl mx-auto flex">
        <aside className={`fixed sm:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full sm:translate-x-0'} pt-16 sm:pt-0`}>
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link key={item.path} to={item.path} onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}`}>
                  <Icon className="w-5 h-5" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </aside>
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
