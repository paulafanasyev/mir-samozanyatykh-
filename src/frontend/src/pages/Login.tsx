import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import apiClient from '../api/client'
import { Mail, Lock, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [requires2FA, setRequires2FA] = useState(false)
  const [tempToken, setTempToken] = useState('')
  const [code, setCode] = useState('')
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const body = new URLSearchParams({ email, password })
      const res = await apiClient.post('/api/auth/login', body, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
      if (res.data.requires_2fa) {
        setTempToken(res.data.temp_token)
        setRequires2FA(true)
        toast.success('Введите код двухфакторной аутентификации')
        return
      }
      useAuthStore.getState().setToken(res.data.access_token)
      const me = await apiClient.get('/api/users/me')
      setAuth(me.data, res.data.access_token)
      toast.success('Добро пожаловать!')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  const handle2FASubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const body = new URLSearchParams({ temp_token: tempToken, code })
      const res = await apiClient.post('/api/auth/login/2fa', body, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
      useAuthStore.getState().setToken(res.data.access_token)
      const me = await apiClient.get('/api/users/me')
      setAuth(me.data, res.data.access_token)
      toast.success('Вход выполнен')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Неверный код 2FA')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-[calc(100vh-72px)] px-4 py-10 sm:py-14">
      <div className="mx-auto grid w-full max-w-5xl items-center gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
        <section className="hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-orange-950 p-10 text-white shadow-xl lg:block">
          <p className="mb-3 text-sm font-semibold text-orange-300">Мир Самозанятых</p>
          <h1 className="text-4xl font-black leading-tight">Всё необходимое для вашей работы</h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">Безопасный кабинет самозанятого: сделки, документы, финансы и помощь Светланы.</p>
          <div className="mt-8 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-xl">✦</div>
            <div><div className="font-bold">Светлана</div><div className="text-sm text-slate-400">Ваш ИИ-ассистент</div></div>
          </div>
        </section>

        <section className="w-full rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
          <div className="mb-7 text-center">
            <p className="text-sm font-semibold text-orange-600">Мир Самозанятых</p>
            <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950">Вход</h2>
            <p className="mt-2 text-sm text-slate-500">Войдите в свой рабочий кабинет</p>
          </div>

          {requires2FA ? (
            <form onSubmit={handle2FASubmit} className="space-y-4">
              <div><label htmlFor="login-2fa" className="mb-1.5 block text-sm font-semibold text-slate-700">Код 2FA</label><input id="login-2fa" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" maxLength={6} required className="input text-center text-lg tracking-[.35em]" placeholder="123456" /></div>
              <button disabled={loading || code.length !== 6} className="btn-brand w-full py-3">{loading ? 'Проверка…' : 'Подтвердить'}</button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="login-email" className="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
                <div className="relative"><Mail aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input id="login-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" placeholder="you@example.com" className="input pl-10" /></div>
              </div>
              <div>
                <label htmlFor="login-password" className="mb-1.5 block text-sm font-semibold text-slate-700">Пароль</label>
                <div className="relative"><Lock aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input id="login-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" className="input pl-10 pr-10" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'} className="absolute right-2 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700">{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
                </div>
              </div>
              <button type="submit" disabled={loading} className="btn-brand w-full py-3">{loading ? 'Вход…' : 'Войти'}</button>
            </form>
          )}

          <p className="mt-5 text-center text-sm"><Link to="/reset-password" className="font-medium text-orange-600 hover:underline">Забыли пароль?</Link></p>
          <p className="mt-4 text-center text-sm text-slate-600">Нет аккаунта? <Link to="/register" className="font-semibold text-orange-600 hover:underline">Зарегистрироваться</Link></p>
        </section>
      </div>
    </main>
  )
}
