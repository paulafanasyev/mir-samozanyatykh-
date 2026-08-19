import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import apiClient from '../api/client'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const [state, setState] = useState<'loading'|'success'|'error'>('loading')
  const [message, setMessage] = useState('Проверяем ссылку…')

  useEffect(() => {
    const token = params.get('token')
    if (!token) { setState('error'); setMessage('Ссылка подтверждения не содержит токен.'); return }
    apiClient.get('/api/auth/verify-email', { params: { token } })
      .then(() => { setState('success'); setMessage('Email успешно подтверждён. Теперь можно войти.'); })
      .catch((e) => { setState('error'); setMessage(e.response?.data?.detail || 'Ссылка недействительна или истекла.'); })
  }, [params])

  return <div className='max-w-md mx-auto bg-white p-8 rounded-xl border border-slate-200 shadow-sm text-center'>
    <h1 className='text-2xl font-bold text-slate-900 mb-4'>Подтверждение email</h1>
    <p className={state === 'success' ? 'text-green-700' : state === 'error' ? 'text-red-700' : 'text-slate-600'}>{message}</p>
    {state !== 'loading' && <Link to='/login' className='inline-block mt-6 bg-orange-600 text-white px-5 py-2 rounded-lg'>Перейти ко входу</Link>}
  </div>
}
