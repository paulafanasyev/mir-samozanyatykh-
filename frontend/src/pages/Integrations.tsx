import { useState, useEffect } from 'react'
import { useAuthStore } from '../stores/authStore'
import { api } from '../api/client'
import {
  Plug, Key, Webhook, Download, Upload, Copy, CheckCircle,
  X, AlertTriangle, Trash2, Plus, Eye, EyeOff, RefreshCw,
  FileText, FileSpreadsheet, FileJson, ChevronRight, Clock,
  CheckCircle2, XCircle, ExternalLink
} from 'lucide-react'

interface ApiKey {
  id: number
  name: string
  key_prefix: string
  scopes: string[]
  last_used_at: string | null
  expires_at: string | null
  is_active: boolean
  created_at: string
}

interface WebhookItem {
  id: number
  url: string
  events: string[]
  is_active: boolean
  failure_count: number
  last_delivered_at: string | null
  last_error: string | null
  created_at: string
}

interface Delivery {
  id: number
  event: string
  success: boolean
  response_status: number | null
  duration_ms: number | null
  created_at: string
}

interface ImportResult {
  total_rows: number
  imported: number
  errors: { row: number; error: string }[]
  warnings: string[]
}

export default function Integrations() {
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'apikeys' | 'webhooks' | 'export' | 'import'>('apikeys')
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [webhooks, setWebhooks] = useState<WebhookItem[]>([])
  const [deliveries, setDeliveries] = useState<Delivery[]>([])
  const [selectedWebhook, setSelectedWebhook] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  // API Key form
  const [showKeyForm, setShowKeyForm] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [newKeyScopes, setNewKeyScopes] = useState<string[]>(['read'])
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Webhook form
  const [showWebhookForm, setShowWebhookForm] = useState(false)
  const [newWebhookUrl, setNewWebhookUrl] = useState('')
  const [newWebhookEvents, setNewWebhookEvents] = useState<string[]>(['invoice.paid'])

  // Import
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importType, setImportType] = useState<'products' | 'clients'>('products')
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [importing, setImporting] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      if (activeTab === 'apikeys') {
        const res = await api.get('/api-keys/')
        setApiKeys(res.data)
      } else if (activeTab === 'webhooks') {
        const res = await api.get('/webhooks/')
        setWebhooks(res.data)
      }
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка загрузки')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const createApiKey = async () => {
    if (!newKeyName.trim()) return
    try {
      const res = await api.post('/api-keys/', {
        name: newKeyName,
        scopes: newKeyScopes,
        expires_days: 365,
      })
      setCreatedKey(res.data.key)
      setNewKeyName('')
      setNewKeyScopes(['read'])
      fetchData()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка создания ключа')
    }
  }

  const deleteApiKey = async (id: number) => {
    if (!confirm('Отозвать ключ?')) return
    try {
      await api.delete(`/api-keys/${id}`)
      fetchData()
    } catch (e) {
      // ignore
    }
  }

  const createWebhook = async () => {
    if (!newWebhookUrl.trim()) return
    try {
      await api.post('/webhooks/', {
        url: newWebhookUrl,
        events: newWebhookEvents,
      })
      setShowWebhookForm(false)
      setNewWebhookUrl('')
      setNewWebhookEvents(['invoice.paid'])
      fetchData()
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка создания вебхука')
    }
  }

  const testWebhook = async (id: number) => {
    try {
      const res = await api.post(`/webhooks/${id}/test`)
      setMessage(res.data.success ? 'Тест успешен!' : `Ошибка: ${res.data.status_code}`)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка теста')
    }
  }

  const deleteWebhook = async (id: number) => {
    if (!confirm('Удалить вебхук?')) return
    try {
      await api.delete(`/webhooks/${id}`)
      fetchData()
    } catch (e) {
      // ignore
    }
  }

  const fetchDeliveries = async (webhookId: number) => {
    try {
      const res = await api.get(`/webhooks/${webhookId}/deliveries`)
      setDeliveries(res.data)
      setSelectedWebhook(webhookId)
    } catch (e) {
      // ignore
    }
  }

  const handleExport = async (type: string, format: string) => {
    try {
      const res = await api.get(`/export/${type}?format=${format}`, {
        responseType: format === 'csv' ? 'blob' : 'json',
      })
      if (format === 'csv') {
        const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${type}_export_${new Date().toISOString().slice(0, 10)}.csv`
        link.click()
      } else {
        const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `${type}_export_${new Date().toISOString().slice(0, 10)}.json`
        link.click()
      }
      setMessage(`Экспорт ${type} завершён`)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка экспорта')
    }
  }

  const handleImport = async () => {
    if (!importFile) return
    setImporting(true)
    const formData = new FormData()
    formData.append('file', importFile)
    try {
      const res = await api.post(`/import/${importType}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setImportResult(res.data)
      setImportFile(null)
    } catch (e: any) {
      setError(e.response?.data?.message || 'Ошибка импорта')
    } finally {
      setImporting(false)
    }
  }

  const allEvents = [
    'invoice.paid', 'invoice.created', 'invoice.sent',
    'deal.won', 'deal.lost', 'deal.created',
    'client.created', 'task.created', 'task.completed',
    'product.created', 'payment.received',
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Plug className="w-7 h-7 text-blue-600" />
          Интеграции
        </h1>
        <p className="text-slate-500 mt-1">API ключи, вебхуки, экспорт и импорт данных</p>
      </div>

      {/* Tabs */}
      <div className="flex bg-white rounded-lg border border-slate-200 overflow-hidden">
        {([
          { key: 'apikeys', label: 'API Ключи', icon: Key },
          { key: 'webhooks', label: 'Вебхуки', icon: Webhook },
          { key: 'export', label: 'Экспорт', icon: Download },
          { key: 'import', label: 'Импорт', icon: Upload },
        ] as const).map((t) => {
          const Icon = t.icon
          return (
            <button
              key={t.key}
              onClick={() => { setActiveTab(t.key); setError(''); setMessage(''); setImportResult(null) }}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === t.key ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          )
        })}
      </div>

      {message && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2 text-green-700">
          <CheckCircle className="w-5 h-5" />
          {message}
          <button onClick={() => setMessage('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-5 h-5" />
          {error}
          <button onClick={() => setError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* API KEYS TAB */}
      {activeTab === 'apikeys' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-900">API Ключи</h2>
            <button
              onClick={() => setShowKeyForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Создать ключ
            </button>
          </div>

          {createdKey && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-800 font-medium">
                <AlertTriangle className="w-5 h-5" />
                Скопируйте ключ сейчас — он больше не будет показан!
              </div>
              <div className="flex gap-2">
                <code className="flex-1 bg-white border border-amber-200 rounded-lg px-3 py-2 text-sm font-mono break-all">
                  {createdKey}
                </code>
                <button
                  onClick={() => { navigator.clipboard.writeText(createdKey); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
                  className="px-3 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700"
                >
                  {copied ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <button onClick={() => setCreatedKey(null)} className="text-sm text-amber-700 hover:underline">
                Я сохранил ключ
              </button>
            </div>
          )}

          {apiKeys.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
              <Key className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>У вас пока нет API ключей</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Название</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Ключ</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Права</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Статус</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Действия</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {apiKeys.map((key) => (
                    <tr key={key.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium text-slate-900">{key.name}</td>
                      <td className="px-4 py-3">
                        <code className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">{key.key_prefix}...</code>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap">
                          {key.scopes.map((s) => (
                            <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">{s}</span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${key.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                          {key.is_active ? 'Активен' : 'Отозван'}
                        </span>
                        {key.expires_at && (
                          <div className="text-xs text-slate-400 mt-1">
                            До {new Date(key.expires_at).toLocaleDateString('ru-RU')}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => deleteApiKey(key.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                          title="Отозвать"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {showKeyForm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Новый API ключ</h3>
                  <button onClick={() => setShowKeyForm(false)}><X className="w-5 h-5 text-slate-400" /></button>
                </div>
                <div>
                  <label className="text-sm text-slate-600">Название</label>
                  <input
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="Например: Integration Bot"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-600">Права доступа</label>
                  <div className="flex gap-3 mt-2">
                    {['read', 'write', 'admin'].map((s) => (
                      <label key={s} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={newKeyScopes.includes(s)}
                          onChange={(e) => {
                            if (e.target.checked) setNewKeyScopes([...newKeyScopes, s])
                            else setNewKeyScopes(newKeyScopes.filter(x => x !== s))
                          }}
                        />
                        {s}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={createApiKey} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Создать</button>
                  <button onClick={() => setShowKeyForm(false)} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">Отмена</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* WEBHOOKS TAB */}
      {activeTab === 'webhooks' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-900">Вебхуки</h2>
            <button
              onClick={() => setShowWebhookForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Добавить вебхук
            </button>
          </div>

          {webhooks.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-500">
              <Webhook className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>У вас пока нет вебхуков</p>
            </div>
          ) : (
            <div className="space-y-3">
              {webhooks.map((wh) => (
                <div key={wh.id} className={`bg-white rounded-xl border p-4 ${wh.is_active ? 'border-slate-200' : 'border-red-200 bg-red-50/30'}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${wh.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="font-medium text-slate-900 text-sm">{wh.url}</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {wh.events.map((e) => (
                          <span key={e} className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">{e}</span>
                        ))}
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                        {wh.last_delivered_at && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            Последняя доставка: {new Date(wh.last_delivered_at).toLocaleString('ru-RU')}
                          </span>
                        )}
                        {wh.failure_count > 0 && (
                          <span className="text-red-600 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Ошибок: {wh.failure_count}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button onClick={() => testWebhook(wh.id)} className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg" title="Тест">
                        <RefreshCw className="w-4 h-4" />
                      </button>
                      <button onClick={() => fetchDeliveries(wh.id)} className="p-1.5 text-slate-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg" title="История">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button onClick={() => deleteWebhook(wh.id)} className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg" title="Удалить">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {selectedWebhook === wh.id && deliveries.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100">
                      <h4 className="text-xs font-medium text-slate-500 mb-2">История доставок</h4>
                      <div className="space-y-1">
                        {deliveries.map((d) => (
                          <div key={d.id} className="flex items-center gap-2 text-xs">
                            {d.success ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <XCircle className="w-3 h-3 text-red-500" />}
                            <span className="text-slate-600">{d.event}</span>
                            <span className="text-slate-400">{d.response_status}</span>
                            {d.duration_ms && <span className="text-slate-400">{d.duration_ms}мс</span>}
                            <span className="text-slate-400 ml-auto">{new Date(d.created_at).toLocaleString('ru-RU')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {showWebhookForm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Новый вебхук</h3>
                  <button onClick={() => setShowWebhookForm(false)}><X className="w-5 h-5 text-slate-400" /></button>
                </div>
                <div>
                  <label className="text-sm text-slate-600">URL</label>
                  <input
                    value={newWebhookUrl}
                    onChange={(e) => setNewWebhookUrl(e.target.value)}
                    placeholder="https://example.com/webhook"
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-600">События</label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {allEvents.map((e) => (
                      <label key={e} className={`text-xs px-2 py-1 rounded-full border cursor-pointer ${
                        newWebhookEvents.includes(e) ? 'bg-purple-100 border-purple-300 text-purple-700' : 'bg-white border-slate-200 text-slate-600'
                      }`}>
                        <input
                          type="checkbox"
                          className="hidden"
                          checked={newWebhookEvents.includes(e)}
                          onChange={(ev) => {
                            if (ev.target.checked) setNewWebhookEvents([...newWebhookEvents, e])
                            else setNewWebhookEvents(newWebhookEvents.filter(x => x !== e))
                          }}
                        />
                        {e}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={createWebhook} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Создать</button>
                  <button onClick={() => setShowWebhookForm(false)} className="flex-1 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">Отмена</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* EXPORT TAB */}
      {activeTab === 'export' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Экспорт данных</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { type: 'products', label: 'Продукты', desc: 'Все продукты с ценами' },
              { type: 'invoices', label: 'Счета', desc: 'Все счета и позиции' },
              { type: 'clients', label: 'Клиенты', desc: 'База клиентов' },
              { type: 'deals', label: 'Сделки', desc: 'Все сделки CRM' },
              { type: 'tasks', label: 'Задачи', desc: 'Все задачи' },
              { type: 'all', label: 'Всё', desc: 'Полный JSON экспорт' },
            ].map((item) => (
              <div key={item.type} className="bg-white rounded-xl border border-slate-200 p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-slate-900">{item.label}</span>
                </div>
                <p className="text-sm text-slate-500">{item.desc}</p>
                <div className="flex gap-2">
                  {item.type !== 'all' && (
                    <>
                      <button
                        onClick={() => handleExport(item.type, 'csv')}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm hover:bg-slate-200"
                      >
                        <FileSpreadsheet className="w-4 h-4" />
                        CSV
                      </button>
                      <button
                        onClick={() => handleExport(item.type, 'json')}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm hover:bg-slate-200"
                      >
                        <FileJson className="w-4 h-4" />
                        JSON
                      </button>
                    </>
                  )}
                  {item.type === 'all' && (
                    <button
                      onClick={() => handleExport(item.type, 'json')}
                      className="w-full flex items-center justify-center gap-1.5 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                    >
                      <Download className="w-4 h-4" />
                      Скачать JSON
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* IMPORT TAB */}
      {activeTab === 'import' && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Импорт данных</h2>
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
            <div>
              <label className="text-sm text-slate-600">Тип данных</label>
              <select
                value={importType}
                onChange={(e) => setImportType(e.target.value as 'products' | 'clients')}
                className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                <option value="products">Продукты</option>
                <option value="clients">Клиенты</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-600">CSV файл</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
              <p className="text-xs text-slate-400 mt-1">
                {importType === 'products'
                  ? 'Ожидаемые колонки: name, description, price, unit, sku'
                  : 'Ожидаемые колонки: name, email, phone, company, inn'}
              </p>
            </div>
            <button
              onClick={handleImport}
              disabled={!importFile || importing}
              className="w-full flex items-center justify-center gap-2 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              <Upload className="w-4 h-4" />
              {importing ? 'Импорт...' : 'Импортировать'}
            </button>
          </div>

          {importResult && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
              <h3 className="font-medium text-slate-900">Результат импорта</h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-green-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">{importResult.imported}</div>
                  <div className="text-xs text-slate-500">Импортировано</div>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-slate-700">{importResult.total_rows}</div>
                  <div className="text-xs text-slate-500">Всего строк</div>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold text-red-600">{importResult.errors.length}</div>
                  <div className="text-xs text-slate-500">Ошибок</div>
                </div>
              </div>
              {importResult.errors.length > 0 && (
                <div className="max-h-40 overflow-y-auto space-y-1">
                  {importResult.errors.map((err, i) => (
                    <div key={i} className="text-xs text-red-600 flex items-center gap-1">
                      <XCircle className="w-3 h-3" />
                      Строка {err.row}: {err.error}
                    </div>
                  ))}
                </div>
              )}
              {importResult.warnings.length > 0 && (
                <div className="space-y-1">
                  {importResult.warnings.map((w, i) => (
                    <div key={i} className="text-xs text-amber-600 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {w}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
