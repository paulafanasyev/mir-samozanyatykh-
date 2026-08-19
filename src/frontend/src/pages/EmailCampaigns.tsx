import type { FormEvent } from 'react'
import { useState, useEffect } from 'react'
import { Mail, Send, Users, Eye, Plus, Trash2, BarChart3, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '../api/client'

interface Campaign {

id: number

name: string

subject: string

status: string

sent_count: number

opened_count: number

created_at: string
}

interface Client {

id: number

name: string

email: string

selected: boolean
}

export default function EmailCampaigns() {

const [campaigns, setCampaigns] = useState<Campaign[]>([])

const [clients, setClients] = useState<Client[]>([])

const [showForm, setShowForm] = useState(false)

const [loading, setLoading] = useState(false)

const [selectAll, setSelectAll] = useState(false)


const [formData, setFormData] = useState({

name: '',

subject: '',

body: '',

send_now: true,

})


useEffect(() => {

fetchCampaigns()

fetchClients()

}, [])


const fetchCampaigns = async () => {

try {

const res = await apiClient.get('/api/email/campaigns')

setCampaigns(res.data?.campaigns || [])

} catch (e) {

console.error(e)

}

}


const fetchClients = async () => {

try {

const res = await apiClient.get('/api/crm/clients?per_page=100')

setClients((res.data?.items || []).map((c: any) => ({ ...c, selected: false })))

} catch (e) {

console.error(e)

}

}


const handleSubmit = async (e: FormEvent) => {

e.preventDefault()

setLoading(true)

try {

const selectedIds = clients.filter(c => c.selected).map(c => c.id)

await apiClient.post('/api/email/send', {

...formData,

client_ids: selectedIds.length > 0 ? selectedIds : undefined,

})

setShowForm(false)

setFormData({ name: '', subject: '', body: '', send_now: true })

setSelectAll(false)

setClients(clients.map(c => ({ ...c, selected: false })))

fetchCampaigns()

} catch (e: any) {

alert(e.response?.data?.detail || 'Ошибка отправки')

} finally {

setLoading(false)

}

}


const toggleSelectAll = () => {

const newVal = !selectAll

setSelectAll(newVal)

setClients(clients.map(c => ({ ...c, selected: newVal })))

}


const toggleClient = (id: number) => {

setClients(clients.map(c => c.id === id ? { ...c, selected: !c.selected } : c))

}


const selectedCount = clients.filter(c => c.selected).length


return (

<div className="max-w-5xl mx-auto space-y-6">

{/* Header */}

<div className="flex items-center justify-between">

<div className="flex items-center gap-3">

<Mail className="w-8 h-8 text-orange-600" />

<div>

<h1 className="text-2xl font-bold text-slate-800">Email-rassyilki</h1>

<p className="text-slate-500 text-sm">Massovye rassyilki klientam</p>

</div>

</div>

<button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700">

<Plus className="w-4 h-4" />

Novaya rassyilka

</button>

</div>


{/* Stats */}

<div className="grid grid-cols-1 sm:grid-cols-3 gap-4">

<div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">

<div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">

<Send className="w-5 h-5 text-orange-600" />

</div>

<div>

<p className="text-sm text-slate-500">Otpravleno</p>

<p className="text-xl font-bold text-slate-800">{campaigns.reduce((s, c) => s + c.sent_count, 0)}</p>

</div>

</div>

<div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">

<div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">

<Eye className="w-5 h-5 text-green-600" />

</div>

<div>

<p className="text-sm text-slate-500">Otkrytiy</p>

<p className="text-xl font-bold text-slate-800">{campaigns.reduce((s, c) => s + c.opened_count, 0)}</p>

</div>

</div>

<div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-3">

<div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">

<BarChart3 className="w-5 h-5 text-amber-600" />

</div>

<div>

<p className="text-sm text-slate-500">Konversiya</p>

<p className="text-xl font-bold text-slate-800">

{campaigns.length > 0

? Math.round((campaigns.reduce((s, c) => s + c.opened_count, 0) / Math.max(campaigns.reduce((s, c) => s + c.sent_count, 0), 1)) * 100)

: 0}%

</p>

</div>

</div>

</div>


{/* Form */}

{showForm && (

<div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">

<h3 className="font-semibold text-slate-800">Novaya email-rassyilka</h3>

<form onSubmit={handleSubmit} className="space-y-4">

<div className="grid grid-cols-1 md:grid-cols-2 gap-4">

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Nazvanie kampanii</label>

<input type="text" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="Vesennaya aktsiya" required />

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Tema pisma</label>

<input type="text" value={formData.subject} onChange={e => setFormData({ ...formData, subject: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="Spetsialnoe predlozhenie dlya vas" required />

</div>

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Tekst pisma (HTML podderzhivaetsya)</label>

<textarea value={formData.body} onChange={e => setFormData({ ...formData, body: e.target.value })} rows={6} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="<h1>Zdravstvuyte!</h1><p>My podgotovili dlya vas...</p>" required />

</div>


{/* Client Selection */}

<div>

<div className="flex items-center justify-between mb-2">

<label className="text-sm font-medium text-slate-700 flex items-center gap-2">

<Users className="w-4 h-4" />

Poluchateli ({selectedCount} vybrano)

</label>

<button type="button" onClick={toggleSelectAll} className="text-sm text-orange-600 hover:text-orange-700">

{selectAll ? 'Otmenit vse' : 'Vybrat vse'}

</button>

</div>

<div className="max-h-48 overflow-y-auto border border-slate-200 rounded-lg">

{clients.length === 0 ? (

<div className="p-4 text-center text-slate-400 text-sm">Net klientov s email</div>

) : (

<table className="w-full text-sm">

<thead className="bg-slate-50 sticky top-0">

<tr>

<th className="px-3 py-2 text-left w-8">

<input type="checkbox" checked={selectAll} onChange={toggleSelectAll} />

</th>

<th className="px-3 py-2 text-left text-slate-500 font-medium">Imya</th>

<th className="px-3 py-2 text-left text-slate-500 font-medium">Email</th>

</tr>

</thead>

<tbody>

{clients.map(c => (

<tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">

<td className="px-3 py-2">

<input type="checkbox" checked={c.selected} onChange={() => toggleClient(c.id)} />

</td>

<td className="px-3 py-2 text-slate-700">{c.name}</td>

<td className="px-3 py-2 text-slate-500">{c.email}</td>

</tr>

))}

</tbody>

</table>

)}

</div>

<p className="text-xs text-slate-400 mt-1">Esli ne vybrat nikogo — otpravka vsem klientam</p>

</div>


<div className="flex gap-2">

<button type="submit" disabled={loading} className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 disabled:opacity-50">

{loading ? 'Otpravka...' : 'Otpravit rassyilku'}

</button>

<button type="button" onClick={() => setShowForm(false)} className="border border-slate-300 text-slate-600 px-6 py-2 rounded-lg hover:bg-slate-50">Otmena</button>

</div>

</form>

</div>

)}


{/* Campaigns List */}

<div className="bg-white border border-slate-200 rounded-xl overflow-hidden">

<div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">

<Mail className="w-4 h-4 text-slate-400" />

<span className="font-medium text-slate-700">Istoriya rassylok</span>

</div>

{campaigns.length === 0 ? (

<div className="p-8 text-center text-slate-400">Poka net otpravlennykh rassylok</div>

) : (

<div className="overflow-x-auto">

<table className="w-full text-sm">

<thead className="bg-slate-50">

<tr>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Kampaniya</th>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Tema</th>

<th className="text-center px-4 py-2 text-slate-500 font-medium">Status</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Otpravleno</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Otkrytiy</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Konversiya</th>

</tr>

</thead>

<tbody>

{campaigns.map(c => (

<tr key={c.id} className="border-t border-slate-100 hover:bg-slate-50">

<td className="px-4 py-3 font-medium text-slate-800">{c.name}</td>

<td className="px-4 py-3 text-slate-600">{c.subject}</td>

<td className="px-4 py-3 text-center">

<span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${c.status === 'sent' ? 'bg-green-100 text-green-700' : c.status === 'draft' ? 'bg-slate-100 text-slate-600' : 'bg-orange-100 text-orange-700'}`}>

{c.status === 'sent' ? <CheckCircle className="w-3 h-3" /> : c.status === 'draft' ? <XCircle className="w-3 h-3" /> : <Send className="w-3 h-3" />}

{c.status}

</span>

</td>

<td className="px-4 py-3 text-right text-slate-600">{c.sent_count}</td>

<td className="px-4 py-3 text-right text-slate-600">{c.opened_count}</td>

<td className="px-4 py-3 text-right font-medium text-slate-800">

{c.sent_count > 0 ? Math.round((c.opened_count / c.sent_count) * 100) : 0}%

</td>

</tr>

))}

</tbody>

</table>

</div>

)}

</div>

</div>

)
}
