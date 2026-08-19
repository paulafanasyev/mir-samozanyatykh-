import { FormEvent, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import apiClient from '../api/client'

export default function ResetPassword() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') || ''
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const requestReset = async (e: FormEvent) => {
    e.preventDefault(); setLoading(true); setError(''); setMessage('')
    try { const r = await apiClient.post('/api/auth/password-reset', { email }); setMessage(r.data.message) }
    catch (e: any) { setError(e.response?.data?.detail || 'Не удалось отправить запрос') }
    finally { setLoading(false) }
  }

  const confirmReset = async (e: FormEvent) => {
    e.preventDefault(); setLoading(true); setError(''); setMessage('')
    if (password !== confirmation) { setError('Пароли не совпадают'); setLoading(false); return }
    try { await apiClient.post('/api/auth/password-reset/confirm', { token, new_password: password }); setMessage('Пароль изменён. Переходим ко входу…'); setTimeout(() => navigate('/login'), 800) }
    catch (e: any) { setError(e.response?.data?.detail || 'Ссылка недействительна или истекла') }
    finally { setLoading(false) }
  }

  return <div className='max-w-md mx-auto bg-white p-8 rounded-xl border border-slate-200 shadow-sm'>
    <h1 className='text-2xl font-bold text-slate-900 mb-6 text-center'>{token ? 'Новый пароль' : 'Сброс пароля'}</h1>
    {token ? <form onSubmit={confirmReset} className='space-y-4'>
      <input type='password' required minLength={12} value={password} onChange={e=>setPassword(e.target.value)} placeholder='Новый пароль' className='w-full border rounded-lg px-3 py-2' />
      <input type='password' required minLength={12} value={confirmation} onChange={e=>setConfirmation(e.target.value)} placeholder='Повторите пароль' className='w-full border rounded-lg px-3 py-2' />
      <button disabled={loading} className='w-full bg-orange-600 text-white py-2 rounded-lg'>{loading ? 'Сохранение…' : 'Изменить пароль'}</button>
    </form> : <form onSubmit={requestReset} className='space-y-4'>
      <input type='email' required value={email} onChange={e=>setEmail(e.target.value)} placeholder='Email' className='w-full border rounded-lg px-3 py-2' />
      <button disabled={loading} className='w-full bg-orange-600 text-white py-2 rounded-lg'>{loading ? 'Отправка…' : 'Отправить ссылку'}</button>
    </form>}
    {message && <p className='mt-4 text-green-700 text-sm'>{message}</p>}
    {error && <p className='mt-4 text-red-700 text-sm'>{error}</p>}
    <p className='text-center text-sm mt-5'><Link to='/login' className='text-orange-600 hover:underline'>Вернуться ко входу</Link></p>
  </div>
}
