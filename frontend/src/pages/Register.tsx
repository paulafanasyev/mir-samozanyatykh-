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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await apiClient.post('/api/auth/register', form)
      toast.success('Registratsiya uspeshna! Proverte email.')
      navigate('/login')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || ' Oshibka registratsii')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900 mb-6 text-center">Registratsiya</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Imya</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input value={form.full_name} onChange={(e) => setForm({...form, full_name: e.target.value})} required
                className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} required
                className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Parol</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} required minLength={8}
                className="w-full pl-10 pr-10 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {loading ? 'Sozdanie...' : 'Zaregistrirovatsya'}
          </button>
        </form>
        <p className="text-center text-sm text-slate-600 mt-4">
          Uzhe est akkaunt? <Link to="/login" className="text-blue-600 hover:underline">Voyti</Link>
        </p>
      </div>
    </div>
  )
}
