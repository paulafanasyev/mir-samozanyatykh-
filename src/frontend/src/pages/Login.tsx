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

toast.success('Dobro pozhalovat!')

navigate('/dashboard')

} catch (err: any) {

toast.error(err.response?.data?.detail || ' Oshibka vvoda')

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

<div className="max-w-md mx-auto">

<div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">

<h1 className="text-2xl font-bold text-slate-900 mb-6 text-center">Vkhod</h1>

{requires2FA ? (
<form onSubmit={handle2FASubmit} className="space-y-4">
<div><label className="block text-sm font-medium mb-1">Код 2FA</label><input value={code} onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" maxLength={6} required className="w-full border rounded-lg px-3 py-2" placeholder="123456" /></div>
<button disabled={loading || code.length !== 6} className="w-full bg-orange-600 text-white rounded-lg py-2 disabled:opacity-50">{loading ? 'Проверка...' : 'Подтвердить'}</button>
</form>
) : (
<form onSubmit={handleSubmit} className="space-y-4">

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Email</label>

<div className="relative">

<Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required

className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none" />

</div>

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Parol</label>

<div className="relative">

<Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />

<input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} required

className="w-full pl-10 pr-10 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none" />

<button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">

{showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}

</button>

</div>

</div>

<button type="submit" disabled={loading}

className="w-full bg-orange-600 text-white py-2.5 rounded-lg font-medium hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">

{loading ? 'Vkhod...' : 'Voyti'}

</button>

</form>
)}

<p className="text-center text-sm mt-3"><Link to="/reset-password" className="text-orange-600 hover:underline">Забыли пароль?</Link></p>

<p className="text-center text-sm text-slate-600 mt-4">

Net akkaunta? <Link to="/register" className="text-orange-600 hover:underline">Zaregistrirovatsya</Link>

</p>

</div>

</div>

)
}
