import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { FileSignature, Download, Plus } from 'lucide-react'
import toast from 'react-hot-toast'

interface Contract {

id: number

template_type: string

title: string | null

status: string

signed_at: string | null

created_at: string
}

export default function Contracts() {

const [contracts, setContracts] = useState<Contract[]>([])

const [templates, setTemplates] = useState<any[]>([])

const [loading, setLoading] = useState(true)


useEffect(() => {

Promise.all([

apiClient.get('/api/contracts/my'),

apiClient.get('/api/contracts/templates'),

]).then(([cRes, tRes]) => {

setContracts(cRes.data)

setTemplates(tRes.data)

setLoading(false)

}).catch(() => { toast.error(' Oshibka zagruzki'); setLoading(false) })

}, [])


if (loading) return <div className="text-center py-12">Zagruzka...</div>


return (

<div className="space-y-6">

<div className="flex justify-between items-center">

<h1 className="text-2xl font-bold text-slate-900">Dogovory</h1>

<button className="bg-orange-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-orange-700"><Plus className="w-4 h-4" /> Novyy dogovor</button>

</div>

<div className="grid sm:grid-cols-2 gap-4">

{templates.map((t) => (

<div key={t.id} className="bg-white p-5 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">

<div className="flex items-center gap-3 mb-2"><FileSignature className="w-5 h-5 text-orange-600" /><h3 className="font-semibold text-slate-800">{t.name}</h3></div>

<p className="text-sm text-slate-600 mb-3">{t.category}</p>

<button onClick={async () => { try { const templateType = t.template_type || t.type || t.category; await apiClient.post('/api/contracts/generate', { template_id: templateType, variables: {} }); toast.success('Договор создан'); const r = await apiClient.get('/api/contracts/my'); setContracts(r.data); } catch (e:any) { toast.error(e?.response?.data?.detail || 'Заполните поля договора'); } }} className="text-sm text-orange-600 hover:underline flex items-center gap-1"><Download className="w-3 h-3" /> Sozdat</button>

</div>

))}

</div>

<h2 className="text-lg font-semibold text-slate-800">Moi dogovory</h2>

<div className="space-y-2">

{contracts.map((c) => (

<div key={c.id} className="bg-white p-4 rounded-xl border border-slate-200 flex items-center justify-between">

<div><h3 className="font-medium text-slate-800">{c.title || c.template_type}</h3><span className="text-xs text-slate-500">{c.status}</span></div>

{c.signed_at && <span className="text-xs text-green-600">Podpisan</span>}

</div>

))}

</div>

</div>

)
}
