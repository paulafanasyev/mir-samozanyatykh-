import { useState } from 'react'
import { Receipt, Search, CheckCircle, XCircle, Camera, QrCode, Loader2, Save, AlertTriangle } from 'lucide-react'
import { apiClient } from '../api/client'

interface ReceiptData {
  found: boolean
  receipt_id?: string
  seller_name?: string
  seller_inn?: string
  total_amount?: number
  items?: Array<{ name: string; price: number; quantity: number; sum: number }>
  date?: string
  message: string
}

export default function ReceiptCheck() {
  const [fiscalNumber, setFiscalNumber] = useState('')
  const [fiscalSign, setFiscalSign] = useState('')
  const [date, setDate] = useState('')
  const [sum, setSum] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ReceiptData | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  const formatDateForAPI = (d: string) => {
    const dt = new Date(d)
    const y = dt.getFullYear()
    const m = String(dt.getMonth() + 1).padStart(2, '0')
    const day = String(dt.getDate()).padStart(2, '0')
    const h = String(dt.getHours()).padStart(2, '0')
    const min = String(dt.getMinutes()).padStart(2, '0')
    return `${y}${m}${day}T${h}${min}`
  }

  const handleCheck = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    setSaved(false)

    try {
      const sumKopecks = Math.round(parseFloat(sum) * 100)
      const res = await apiClient.post('/api/fns/check-receipt', {
        fiscal_document_number: fiscalNumber,
        fiscal_sign: fiscalSign,
        date: formatDateForAPI(date),
        sum: sumKopecks,
      })
      setResult(res.data)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка проверки чека')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!result?.found) return
    try {
      await apiClient.post('/api/fns/save-receipt', {
        fns_id: result.receipt_id || `${fiscalNumber}-${fiscalSign}`,
        fiscal_document_number: fiscalNumber,
        fiscal_sign: fiscalSign,
        receipt_date: new Date(date).toISOString(),
        total_amount: result.total_amount || parseFloat(sum),
        seller_name: result.seller_name,
        seller_inn: result.seller_inn,
        items: result.items,
      })
      setSaved(true)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка сохранения')
    }
  }

  const formatMoney = (n: number) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(n || 0)

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Receipt className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Proverka chekov FNS</h1>
          <p className="text-slate-500 text-sm">Proverte podlinnost kassovogo cheka cherez FNS Rossii</p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <form onSubmit={handleCheck} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Nomer fiskalnogo dokumenta (FN)</label>
              <input
                type="text"
                value={fiscalNumber}
                onChange={e => setFiscalNumber(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2"
                placeholder="1234567890"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Fiskalnyy priznak (FP)</label>
              <input
                type="text"
                value={fiscalSign}
                onChange={e => setFiscalSign(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2"
                placeholder="1234567890"
                required
              />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Data i vremya pokupki</label>
              <input
                type="datetime-local"
                value={date}
                onChange={e => setDate(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Summa (rub)</label>
              <input
                type="number"
                step="0.01"
                value={sum}
                onChange={e => setSum(e.target.value)}
                className="w-full border border-slate-300 rounded-lg px-3 py-2"
                placeholder="0.00"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
            {loading ? 'Proverka...' : 'Proverit chek'}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Oshibka</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className={`border rounded-xl p-6 ${result.found ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
          <div className="flex items-center gap-3 mb-4">
            {result.found ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <XCircle className="w-6 h-6 text-amber-600" />
            )}
            <div>
              <h3 className={`font-semibold ${result.found ? 'text-green-800' : 'text-amber-800'}`}>
                {result.found ? 'Chek podtverzhdyon FNS' : 'Chek ne nayden'}
              </h3>
              <p className={`text-sm ${result.found ? 'text-green-600' : 'text-amber-600'}`}>{result.message}</p>
            </div>
          </div>

          {result.found && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-slate-500">Prodavets</p>
                  <p className="font-medium text-slate-800">{result.seller_name || 'Neizvestno'}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-slate-500">INN prodavtsa</p>
                  <p className="font-medium text-slate-800">{result.seller_inn || '-'}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-slate-500">Summa</p>
                  <p className="font-medium text-slate-800">{formatMoney(result.total_amount || 0)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-slate-500">Data</p>
                  <p className="font-medium text-slate-800">{result.date || '-'}</p>
                </div>
              </div>

              {result.items && result.items.length > 0 && (
                <div className="bg-white rounded-lg p-4">
                  <h4 className="font-medium text-slate-800 mb-2">Tovary i uslugi</h4>
                  <div className="space-y-2">
                    {result.items.map((item, i) => (
                      <div key={i} className="flex justify-between text-sm border-b border-slate-100 pb-2 last:border-0">
                        <span className="text-slate-700">{item.name}</span>
                        <span className="text-slate-500">{item.quantity} x {formatMoney(item.price)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!saved ? (
                <button
                  onClick={handleSave}
                  className="w-full flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Save className="w-5 h-5" />
                  Sokhranit chek i sozdat raskhod
                </button>
              ) : (
                <div className="bg-green-100 text-green-800 rounded-lg p-3 text-center font-medium">
                  <CheckCircle className="w-5 h-5 inline mr-2" />
                  Chek sokhranen! Transaktsiya-raskhod sozdana.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <h4 className="font-medium text-blue-800 mb-2 flex items-center gap-2">
          <QrCode className="w-4 h-4" />
          Gde nayti dannye cheka?
        </h4>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>FN i FP napechatany na kassovom cheke</li>
          <li>Data i vremya — vremya pokupki na cheke</li>
          <li>Summa — itogovaya summa cheka</li>
          <li>Mozhno otskanirovat QR-kod na cheke dlya avtozapolneniya (v razrabotke)</li>
        </ul>
      </div>
    </div>
  )
}
