import { useAuthStore } from '../stores/authStore'
import { UserCircle, Mail, Shield, Award } from 'lucide-react'

export default function Profile() {

const user = useAuthStore((s) => s.user)


if (!user) return <div className="text-center py-12">Neobkhodimo voyti</div>


return (

<div className="max-w-2xl mx-auto space-y-6">

<h1 className="text-2xl font-bold text-slate-900">Profil</h1>

<div className="bg-white p-6 rounded-xl border border-slate-200">

<div className="flex items-center gap-4 mb-6">

<div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center"><UserCircle className="w-8 h-8 text-orange-600" /></div>

<div><h2 className="text-xl font-semibold text-slate-800">{user.full_name || 'Polzovatel'}</h2><p className="text-slate-500">{user.email}</p></div>

</div>

<div className="grid sm:grid-cols-2 gap-4">

<div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"><Mail className="w-5 h-5 text-slate-400" /><div><p className="text-xs text-slate-500">Email</p><p className="text-sm font-medium">{user.email}</p></div></div>

<div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"><Shield className="w-5 h-5 text-slate-400" /><div><p className="text-xs text-slate-500">Rol</p><p className="text-sm font-medium">{user.role}</p></div></div>

<div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"><Award className="w-5 h-5 text-slate-400" /><div><p className="text-xs text-slate-500">Tarif</p><p className="text-sm font-medium">{user.tier}</p></div></div>

</div>

</div>

</div>

)
}
