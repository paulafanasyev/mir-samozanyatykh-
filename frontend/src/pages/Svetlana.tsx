import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Send, Bot } from 'lucide-react'
import apiClient from '../api/client'
import toast from 'react-hot-toast'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Svetlana() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Zdravstvuyte! Ya Svetlana, vash pomoshchnik. Chem mogu pomoch?' }
  ])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  useEffect(() => { scrollToBottom() }, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMsg = input.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setInput('')
    setLoading(true)
    try {
      const res = await apiClient.post('/api/svetlana/chat', { message: userMsg })
      setMessages((prev) => [...prev, { role: 'assistant', content: res.data.response }])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Izvinite, proizoshla oshibka. Poprobuyte pozzhe.' }])
    } finally {
      setLoading(false)
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    toast.info(isRecording ? 'Zapis ostanovlena' : 'Govorite...')
  }

  return (
    <div className="max-w-2xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center"><Bot className="w-5 h-5 text-white" /></div>
        <div><h1 className="text-xl font-bold text-slate-900">Svetlana</h1><p className="text-xs text-slate-500">Golosovoy assistent</p></div>
      </div>
      <div className="flex-1 bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-2 rounded-2xl text-sm ${m.role === 'user' ? 'bg-blue-600 text-white rounded-br-md' : 'bg-slate-100 text-slate-800 rounded-bl-md'}`}>{m.content}</div>
            </div>
          ))}
          {loading && <div className="flex justify-start"><div className="bg-slate-100 px-4 py-2 rounded-2xl text-sm text-slate-500">Dumaet...</div></div>}
          <div ref={messagesEndRef} />
        </div>
        <div className="p-3 border-t border-slate-200 flex items-center gap-2">
          <button onClick={toggleRecording} className={`p-2 rounded-full transition-colors ${isRecording ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && sendMessage()} placeholder="Napishite soobshenie..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
          <button onClick={sendMessage} disabled={loading} className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50"><Send className="w-4 h-4" /></button>
        </div>
      </div>
    </div>
  )
}
