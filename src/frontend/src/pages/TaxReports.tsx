import type { FormEvent } from 'react'
import { useState, useEffect } from 'react'
import { Receipt, FileText, AlertTriangle, CheckCircle, Clock, Plus, Calculator, Download, TrendingDown } from 'lucide-react'
import { apiClient } from '../api/client'

interface TaxReport {

id: number

report_type: string

period_start: string

period_end: string

total_income: number

total_expense: number

taxable_amount: number

tax_amount: number

tax_rate_applied: number

deduction_total: number

status: string

risk_level: string

created_at: string
}

interface Deduction {

id: number

deduction_type: string

name: string

amount: number

year: number

status: string
}

export default function TaxReports() {

const [reports, setReports] = useState<TaxReport[]>([])

const [deductions, setDeductions] = useState<Deduction[]>([])

const [showForm, setShowForm] = useState(false)

const [showDeductionForm, setShowDeductionForm] = useState(false)

const [loading, setLoading] = useState(true)


const [formData, setFormData] = useState({

report_type: 'npd_quarterly',

period_start: '',

period_end: '',

})


const [deductionForm, setDeductionForm] = useState({

deduction_type: 'professional',

name: '',

amount: '',

year: new Date().getFullYear(),

})


useEffect(() => {

fetchData()

}, [])


const fetchData = async () => {

setLoading(true)

try {

const [repRes, dedRes] = await Promise.all([

apiClient.get('/api/accounting/tax-reports'),

apiClient.get('/api/accounting/deductions'),

])

setReports(repRes.data || [])

setDeductions(dedRes.data || [])

} catch (e) {

console.error(e)

} finally {

setLoading(false)

}

}


const handleCreateReport = async (e: FormEvent) => {

e.preventDefault()

try {

await apiClient.post('/api/accounting/tax-reports', {

...formData,

period_start: new Date(formData.period_start).toISOString(),

period_end: new Date(formData.period_end).toISOString(),

})

setShowForm(false)

setFormData({ report_type: 'npd_quarterly', period_start: '', period_end: '' })

fetchData()

} catch (e) {

console.error(e)

}

}


const handleCreateDeduction = async (e: FormEvent) => {

e.preventDefault()

try {

await apiClient.post('/api/accounting/deductions', {

...deductionForm,

amount: parseFloat(deductionForm.amount),

})

setShowDeductionForm(false)

setDeductionForm({ deduction_type: 'professional', name: '', amount: '', year: new Date().getFullYear() })

fetchData()

} catch (e) {

console.error(e)

}

}


const submitReport = async (id: number) => {

try {

await apiClient.post(`/api/accounting/tax-reports/${id}/submit`)

fetchData()

} catch (e) {

console.error(e)

}

}


const formatMoney = (n: number) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(n || 0)

const formatDate = (d: string) => new Date(d).toLocaleDateString('ru-RU')


const reportTypeNames: Record<string, string> = {

npd_quarterly: 'NPD (kvartal)',

ndfl_annual: '4-NDFL (godovoy)',

usn: 'USN',

}


const statusColors: Record<string, string> = {

draft: 'bg-slate-100 text-slate-600',

submitted: 'bg-orange-100 text-orange-700',

accepted: 'bg-green-100 text-green-700',

rejected: 'bg-red-100 text-red-700',

}


const riskColors: Record<string, string> = {

low: 'text-green-600',

medium: 'text-amber-600',

high: 'text-red-600',

}


return (

<div className="max-w-6xl mx-auto space-y-6">

{/* Header */}

<div className="flex items-center justify-between">

<div className="flex items-center gap-3">

<Receipt className="w-8 h-8 text-orange-600" />

<div>

<h1 className="text-2xl font-bold text-slate-800">Nalogovye otchety</h1>

<p className="text-slate-500 text-sm">Raschet nalogov, vychety, deklaratsii</p>

</div>

</div>

<div className="flex gap-2">

<button onClick={() => setShowDeductionForm(!showDeductionForm)} className="flex items-center gap-2 border border-slate-300 text-slate-600 px-4 py-2 rounded-lg hover:bg-slate-50">

<TrendingDown className="w-4 h-4" />

Vychet

</button>

<button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700">

<Plus className="w-4 h-4" />

Novyy otchyot

</button>

</div>

</div>


{/* Deduction Form */}

{showDeductionForm && (

<div className="bg-white border border-slate-200 rounded-xl p-6">

<h3 className="font-semibold text-slate-800 mb-4">Novyy nalogovyy vychet</h3>

<form onSubmit={handleCreateDeduction} className="grid grid-cols-1 md:grid-cols-4 gap-4">

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Tip</label>

<select value={deductionForm.deduction_type} onChange={e => setDeductionForm({ ...deductionForm, deduction_type: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2">

<option value="professional">Professionalnyy</option>

<option value="social">Sotsialnyy</option>

<option value="property">Imushchestvennyy</option>

<option value="investment">Investitsionnyy</option>

</select>

</div>

<div className="md:col-span-2">

<label className="block text-sm font-medium text-slate-700 mb-1">Nazvanie</label>

<input type="text" value={deductionForm.name} onChange={e => setDeductionForm({ ...deductionForm, name: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="Opisanie vycheta" required />

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Summa</label>

<input type="number" step="0.01" value={deductionForm.amount} onChange={e => setDeductionForm({ ...deductionForm, amount: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="0.00" required />

</div>

<div className="md:col-span-4 flex gap-2">

<button type="submit" className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700">Sokhranit</button>

<button type="button" onClick={() => setShowDeductionForm(false)} className="border border-slate-300 text-slate-600 px-6 py-2 rounded-lg hover:bg-slate-50">Otmena</button>

</div>

</form>

</div>

)}


{/* Report Form */}

{showForm && (

<div className="bg-white border border-slate-200 rounded-xl p-6">

<h3 className="font-semibold text-slate-800 mb-4">Sozdat nalogovyy otchyot</h3>

<form onSubmit={handleCreateReport} className="grid grid-cols-1 md:grid-cols-3 gap-4">

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Tip otchyota</label>

<select value={formData.report_type} onChange={e => setFormData({ ...formData, report_type: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2">

<option value="npd_quarterly">NPD (kvartal)</option>

<option value="ndfl_annual">4-NDFL (godovoy)</option>

<option value="usn">USN</option>

</select>

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Nachalo perioda</label>

<input type="date" value={formData.period_start} onChange={e => setFormData({ ...formData, period_start: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" required />

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Konets perioda</label>

<input type="date" value={formData.period_end} onChange={e => setFormData({ ...formData, period_end: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" required />

</div>

<div className="md:col-span-3 flex gap-2">

<button type="submit" className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700">Sozdat otchyot</button>

<button type="button" onClick={() => setShowForm(false)} className="border border-slate-300 text-slate-600 px-6 py-2 rounded-lg hover:bg-slate-50">Otmena</button>

</div>

</form>

</div>

)}


{/* Deductions Summary */}

{deductions.length > 0 && (

<div className="bg-white border border-slate-200 rounded-xl p-4">

<h3 className="font-semibold text-slate-800 mb-3 flex items-center gap-2">

<TrendingDown className="w-5 h-5 text-green-600" />

Nalogovye vychety

</h3>

<div className="flex flex-wrap gap-2">

{deductions.map(d => (

<div key={d.id} className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm">

<span className="font-medium text-slate-700">{d.name}</span>

<span className="text-green-600 ml-2 font-medium">{formatMoney(d.amount)}</span>

<span className="text-slate-400 ml-1">({d.deduction_type})</span>

</div>

))}

</div>

</div>

)}


{/* Reports Table */}

<div className="bg-white border border-slate-200 rounded-xl overflow-hidden">

<div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">

<FileText className="w-4 h-4 text-slate-400" />

<span className="font-medium text-slate-700">Nalogovye otchety</span>

<span className="text-sm text-slate-400 ml-auto">{reports.length} otchyotov</span>

</div>

{loading ? (

<div className="p-8 text-center text-slate-400">Zagruzka...</div>

) : reports.length === 0 ? (

<div className="p-8 text-center text-slate-400">Net sozdannykh otchyotov. Sozdayte pervyy otchyot vyше.</div>

) : (

<div className="overflow-x-auto">

<table className="w-full text-sm">

<thead className="bg-slate-50">

<tr>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Tip</th>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Period</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Dokhody</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Raskhody</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Nalog</th>

<th className="text-center px-4 py-2 text-slate-500 font-medium">Status</th>

<th className="text-center px-4 py-2 text-slate-500 font-medium">Risk</th>

<th className="text-center px-4 py-2 text-slate-500 font-medium">Deystviya</th>

</tr>

</thead>

<tbody>

{reports.map(r => (

<tr key={r.id} className="border-t border-slate-100 hover:bg-slate-50">

<td className="px-4 py-3 text-slate-700 font-medium">{reportTypeNames[r.report_type] || r.report_type}</td>

<td className="px-4 py-3 text-slate-600">{formatDate(r.period_start)} — {formatDate(r.period_end)}</td>

<td className="px-4 py-3 text-right text-green-600 font-medium">{formatMoney(r.total_income)}</td>

<td className="px-4 py-3 text-right text-red-600 font-medium">{formatMoney(r.total_expense)}</td>

<td className="px-4 py-3 text-right text-amber-600 font-medium">{formatMoney(r.tax_amount)}</td>

<td className="px-4 py-3 text-center">

<span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[r.status] || 'bg-slate-100 text-slate-600'}`}>

{r.status === 'draft' && <Clock className="w-3 h-3" />}

{r.status === 'submitted' && <CheckCircle className="w-3 h-3" />}

{r.status === 'accepted' && <CheckCircle className="w-3 h-3" />}

{r.status === 'rejected' && <AlertTriangle className="w-3 h-3" />}

{r.status}

</span>

</td>

<td className="px-4 py-3 text-center">

<span className={`text-xs font-medium ${riskColors[r.risk_level] || 'text-slate-600'}`}>

{r.risk_level === 'low' ? 'Nizkiy' : r.risk_level === 'medium' ? 'Sredniy' : 'Vysokiy'}

</span>

</td>

<td className="px-4 py-3 text-center">

{r.status === 'draft' && (

<button onClick={() => submitReport(r.id)} className="text-orange-600 hover:text-orange-700 text-sm font-medium">

Podat

</button>

)}

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
