import type { FormEvent } from 'react'
import { useState, useEffect } from 'react'
import { Calculator, Plus, ArrowUpCircle, ArrowDownCircle, TrendingUp, Wallet, Filter, Search, Trash2, Edit3, FileText } from 'lucide-react'
import { apiClient } from '../api/client'

interface Transaction {

id: number

transaction_type: 'income' | 'expense'

category: string

subcategory?: string

amount: number

currency: string

description?: string

counterparty?: string

transaction_date: string

status: string

source: string
}

interface DashboardStats {

total_income: number

total_expense: number

net_profit: number

tax_estimate: number

overdue_invoices: number

top_expense_categories: Array<{ category: string; amount: number }>

monthly_trend: Array<{ month: string; income: number; expense: number }>
}

export default function Accounting() {

const [transactions, setTransactions] = useState<Transaction[]>([])

const [stats, setStats] = useState<DashboardStats | null>(null)

const [period, setPeriod] = useState('month')

const [filterType, setFilterType] = useState<'all' | 'income' | 'expense'>('all')

const [showForm, setShowForm] = useState(false)

const [loading, setLoading] = useState(true)


const [formData, setFormData] = useState({

transaction_type: 'income' as 'income' | 'expense',

category: '',

amount: '',

description: '',

counterparty: '',

transaction_date: new Date().toISOString().slice(0, 10),

})


useEffect(() => {

fetchData()

}, [period, filterType])


const fetchData = async () => {

setLoading(true)

try {

const [txRes, dashRes] = await Promise.all([

apiClient.get(`/api/accounting/transactions?period=${period}&transaction_type=${filterType !== 'all' ? filterType : ''}`),

apiClient.get(`/api/accounting/dashboard?period=${period}`),

])

setTransactions(txRes.data || [])

setStats(dashRes.data)

} catch (e) {

console.error(e)

} finally {

setLoading(false)

}

}


const handleSubmit = async (e: FormEvent) => {

e.preventDefault()

try {

await apiClient.post('/api/accounting/transactions', {

...formData,

amount: parseFloat(formData.amount),

transaction_date: new Date(formData.transaction_date).toISOString(),

currency: 'RUB',

source: 'manual',

})

setShowForm(false)

setFormData({ transaction_type: 'income', category: '', amount: '', description: '', counterparty: '', transaction_date: new Date().toISOString().slice(0, 10) })

fetchData()

} catch (e) {

console.error(e)

}

}


const deleteTransaction = async (id: number) => {

if (!confirm('Udalit transaktsiyu?')) return

try {

await apiClient.delete(`/api/accounting/transactions/${id}`)

fetchData()

} catch (e) {

console.error(e)

}

}


const formatMoney = (n: number) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(n || 0)

const formatDate = (d: string) => new Date(d).toLocaleDateString('ru-RU')


const incomeTotal = transactions.filter(t => t.transaction_type === 'income').reduce((s, t) => s + t.amount, 0)

const expenseTotal = transactions.filter(t => t.transaction_type === 'expense').reduce((s, t) => s + t.amount, 0)


return (

<div className="max-w-6xl mx-auto space-y-6">

{/* Header */}

<div className="flex items-center justify-between">

<div className="flex items-center gap-3">

<Calculator className="w-8 h-8 text-orange-600" />

<div>

<h1 className="text-2xl font-bold text-slate-800">Bukhgalteriya</h1>

<p className="text-slate-500 text-sm">Uchet dokhodov, raskhodov i nalogov</p>

</div>

</div>

<button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors">

<Plus className="w-4 h-4" />

Novaya transaktsiya

</button>

</div>


{/* Stats Cards */}

<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

<div className="bg-white border border-slate-200 rounded-xl p-4">

<div className="flex items-center gap-3">

<div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">

<ArrowUpCircle className="w-5 h-5 text-green-600" />

</div>

<div>

<p className="text-sm text-slate-500">Dokhody</p>

<p className="text-xl font-bold text-slate-800">{formatMoney(incomeTotal)}</p>

</div>

</div>

</div>

<div className="bg-white border border-slate-200 rounded-xl p-4">

<div className="flex items-center gap-3">

<div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">

<ArrowDownCircle className="w-5 h-5 text-red-600" />

</div>

<div>

<p className="text-sm text-slate-500">Raskhody</p>

<p className="text-xl font-bold text-slate-800">{formatMoney(expenseTotal)}</p>

</div>

</div>

</div>

<div className="bg-white border border-slate-200 rounded-xl p-4">

<div className="flex items-center gap-3">

<div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">

<TrendingUp className="w-5 h-5 text-orange-600" />

</div>

<div>

<p className="text-sm text-slate-500">Pribyl</p>

<p className="text-xl font-bold text-slate-800">{formatMoney(incomeTotal - expenseTotal)}</p>

</div>

</div>

</div>

<div className="bg-white border border-slate-200 rounded-xl p-4">

<div className="flex items-center gap-3">

<div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">

<Wallet className="w-5 h-5 text-amber-600" />

</div>

<div>

<p className="text-sm text-slate-500">Nalog (otsenka)</p>

<p className="text-xl font-bold text-slate-800">{formatMoney(stats?.tax_estimate || 0)}</p>

</div>

</div>

</div>

</div>


{/* Form */}

{showForm && (

<div className="bg-white border border-slate-200 rounded-xl p-6">

<h3 className="font-semibold text-slate-800 mb-4">Novaya transaktsiya</h3>

<form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Tip</label>

<select value={formData.transaction_type} onChange={e => setFormData({ ...formData, transaction_type: e.target.value as 'income' | 'expense' })} className="w-full border border-slate-300 rounded-lg px-3 py-2">

<option value="income">Dokhod</option>

<option value="expense">Raskhod</option>

</select>

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Kategoriya</label>

<input type="text" value={formData.category} onChange={e => setFormData({ ...formData, category: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="napr. uslugi, arenda" required />

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Summa</label>

<input type="number" step="0.01" value={formData.amount} onChange={e => setFormData({ ...formData, amount: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="0.00" required />

</div>

<div>

<label className="block text-sm font-medium text-slate-700 mb-1">Data</label>

<input type="date" value={formData.transaction_date} onChange={e => setFormData({ ...formData, transaction_date: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" required />

</div>

<div className="md:col-span-2">

<label className="block text-sm font-medium text-slate-700 mb-1">Opisanie</label>

<input type="text" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="Opisanie transaktsii" />

</div>

<div className="md:col-span-2">

<label className="block text-sm font-medium text-slate-700 mb-1">Kontragent</label>

<input type="text" value={formData.counterparty} onChange={e => setFormData({ ...formData, counterparty: e.target.value })} className="w-full border border-slate-300 rounded-lg px-3 py-2" placeholder="Imya ili kompaniya" />

</div>

<div className="md:col-span-2 flex gap-2">

<button type="submit" className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700">Sokhranit</button>

<button type="button" onClick={() => setShowForm(false)} className="border border-slate-300 text-slate-600 px-6 py-2 rounded-lg hover:bg-slate-50">Otmena</button>

</div>

</form>

</div>

)}


{/* Filters */}

<div className="flex flex-wrap items-center gap-3">

<div className="flex bg-white border border-slate-200 rounded-lg overflow-hidden">

{[{ k: 'all', l: 'Vse' }, { k: 'income', l: 'Dokhody' }, { k: 'expense', l: 'Raskhody' }].map(t => (

<button key={t.k} onClick={() => setFilterType(t.k as any)} className={`px-4 py-2 text-sm font-medium ${filterType === t.k ? 'bg-orange-50 text-orange-700' : 'text-slate-600 hover:bg-slate-50'}`}>

{t.l}

</button>

))}

</div>

<select value={period} onChange={e => setPeriod(e.target.value)} className="border border-slate-200 rounded-lg px-3 py-2 text-sm">

<option value="week">Nedelya</option>

<option value="month">Mesyats</option>

<option value="quarter">Kvartal</option>

<option value="year">God</option>

</select>

</div>


{/* Transactions Table */}

<div className="bg-white border border-slate-200 rounded-xl overflow-hidden">

<div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">

<FileText className="w-4 h-4 text-slate-400" />

<span className="font-medium text-slate-700">Transaktsii</span>

<span className="text-sm text-slate-400 ml-auto">{transactions.length} zapis</span>

</div>

{loading ? (

<div className="p-8 text-center text-slate-400">Zagruzka...</div>

) : transactions.length === 0 ? (

<div className="p-8 text-center text-slate-400">Net transaktsiy za vybrannyy period</div>

) : (

<div className="overflow-x-auto">

<table className="w-full text-sm">

<thead className="bg-slate-50">

<tr>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Data</th>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Tip</th>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Kategoriya</th>

<th className="text-left px-4 py-2 text-slate-500 font-medium">Opisanie</th>

<th className="text-right px-4 py-2 text-slate-500 font-medium">Summa</th>

<th className="text-center px-4 py-2 text-slate-500 font-medium">Deystviya</th>

</tr>

</thead>

<tbody>

{transactions.map(tx => (

<tr key={tx.id} className="border-t border-slate-100 hover:bg-slate-50">

<td className="px-4 py-3 text-slate-600">{formatDate(tx.transaction_date)}</td>

<td className="px-4 py-3">

<span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${tx.transaction_type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>

{tx.transaction_type === 'income' ? <ArrowUpCircle className="w-3 h-3" /> : <ArrowDownCircle className="w-3 h-3" />}

{tx.transaction_type === 'income' ? 'Dokhod' : 'Raskhod'}

</span>

</td>

<td className="px-4 py-3 text-slate-600">{tx.category}</td>

<td className="px-4 py-3 text-slate-600 max-w-xs truncate">{tx.description || '-'}</td>

<td className={`px-4 py-3 text-right font-medium ${tx.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}`}>

{tx.transaction_type === 'income' ? '+' : '-'}{formatMoney(tx.amount)}

</td>

<td className="px-4 py-3 text-center">

<button onClick={() => deleteTransaction(tx.id)} className="text-slate-400 hover:text-red-600 transition-colors">

<Trash2 className="w-4 h-4" />

</button>

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
