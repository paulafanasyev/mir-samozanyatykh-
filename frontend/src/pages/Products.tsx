import { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { Plus, Pencil, Trash2, Package } from 'lucide-react'
import toast from 'react-hot-toast'

interface Product {
  id: number
  name: string
  description: string | null
  price: number
  unit: string
  sku: string | null
  is_active: boolean
}

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', price: '', unit: 'sht', sku: '' })

  const fetchProducts = async () => {
    try {
      const res = await apiClient.get('/api/sales/products')
      setProducts(res.data)
    } catch {
      toast.error('Ne udalos zagruzit produkty')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProducts() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiClient.post('/api/sales/products', { ...form, price: parseFloat(form.price) })
      toast.success('Produkt sozdan')
      setShowForm(false)
      setForm({ name: '', description: '', price: '', unit: 'sht', sku: '' })
      fetchProducts()
    } catch {
      toast.error(' Oshibka sozdaniya')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Udalit produkt?')) return
    try {
      await apiClient.delete(`/api/sales/products/${id}`)
      toast.success('Produkt udalen')
      fetchProducts()
    } catch {
      toast.error(' Oshibka udaleniya')
    }
  }

  if (loading) return <div className="text-center py-12">Zagruzka...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-900">Produkty i uslugi</h1>
        <button onClick={() => setShowForm(!showForm)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus className="w-4 h-4" /> Dobavit
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white p-6 rounded-xl border border-slate-200 space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <input placeholder="Nazvanie" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} required
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
            <input placeholder="Tsena" type="number" value={form.price} onChange={(e) => setForm({...form, price: e.target.value})} required
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
            <input placeholder="Edinitsa (sht, chas)" value={form.unit} onChange={(e) => setForm({...form, unit: e.target.value})}
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
            <input placeholder="Artikul (SKU)" value={form.sku} onChange={(e) => setForm({...form, sku: e.target.value})}
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <textarea placeholder="Opisanie" value={form.description} onChange={(e) => setForm({...form, description: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500" rows={2} />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Sokhranit</button>
        </form>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Nazvanie</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Tsena</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Ed.</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">SKU</th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">Deystviya</th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Package className="w-4 h-4 text-slate-400" />
                    <span className={p.is_active ? '' : 'line-through text-slate-400'}>{p.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3">{p.price} ₽</td>
                <td className="px-4 py-3">{p.unit}</td>
                <td className="px-4 py-3 text-slate-500">{p.sku || '—'}</td>
                <td className="px-4 py-3 text-right">
                  <button className="text-slate-400 hover:text-blue-600 mr-2"><Pencil className="w-4 h-4" /></button>
                  <button onClick={() => handleDelete(p.id)} className="text-slate-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {products.length === 0 && <div className="text-center py-8 text-slate-500">Poka net produktov</div>}
      </div>
    </div>
  )
}
