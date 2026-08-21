import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { Mail, Lock, User, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Register() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '', phone: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const body = new URLSearchParams(form)
      await apiClient.post('/api/auth/register', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      toast.success('Регистрация прошла успешно. Проверьте почту.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Ошибка регистрации')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-[calc(100vh-72px)] px-4 py-10 sm:py-14">
      <div className="mx-auto grid w-full max-w-5xl items-center gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
        <section className="hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-orange-950 p-10 text-white shadow-xl lg:block">
          <p className="mb-3 text-sm font-semibold text-orange-300">Мир Самозанятых</p>
          <h1 className="text-4xl font-black leading-tight">Рабочее пространство для самозанятого</h1>
          <p className="mt-5 max-w-lg text-base leading-7 text-slate-300">
            Договоры, сделки, финансы, документы и Светлана — в одном защищённом кабинете.
          </p>
          <div className="mt-8 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-xl">✦</div>
            <div><div className="font-bold">Светлана</div><div className="text-sm text-slate-400">Ваш ИИ-ассистент всегда рядом</div></div>
          </div>
        </section>

        <section className="w-full rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
          <div className="mb-7 text-center">
            <p className="text-sm font-semibold text-orange-600">Мир Самозанятых</p>
            <h2 className="mt-1 text-2xl font-black tracking-tight text-slate-950">Регистрация</h2>
            <p className="mt-2 text-sm text-slate-500">Создайте аккаунт и начните работу</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="register-name" className="mb-1.5 block text-sm font-semibold text-slate-700">Имя</label>
              <div className="relative">
                <User aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input id="register-name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required autoComplete="name" placeholder="Ваше имя" className="input pl-10" />
              </div>
            </div>

            <div>
              <label htmlFor="register-email" className="mb-1.5 block text-sm font-semibold text-slate-700">Email</label>
              <div className="relative">
                <Mail aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input id="register-email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required autoComplete="email" placeholder="you@example.com" className="input pl-10" />
              </div>
            </div>

            <div>
              <label htmlFor="register-phone" className="mb-1.5 block text-sm font-semibold text-slate-700">Телефон</label>
              <input id="register-phone" type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} autoComplete="tel" placeholder="+7 900 000-00-00" className="input" />
            </div>

            <div>
              <label htmlFor="register-password" className="mb-1.5 block text-sm font-semibold text-slate-700">Пароль</label>
              <div className="relative">
                <Lock aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input id="register-password" type={showPassword ? 'text' : 'password'} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={12} autoComplete="new-password" placeholder="Не менее 12 символов" className="input pl-10 pr-10" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'} className="absolute right-2 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700">
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-brand w-full py-3">
              {loading ? 'Создание аккаунта…' : 'Зарегистрироваться'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            Уже есть аккаунт? <Link to="/login" className="font-semibold text-orange-600 hover:underline">Войти</Link>
          </p>
        </section>
      </div>
    </main>
  )
}
