'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Mic, MicOff, Bot, Loader2, Trash2, ImagePlus, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '@/app/page'
import { Language, getTranslations, getAgentLabel } from '@/lib/i18n'

interface ChatPanelProps {
  messages: ChatMessage[]
  onSendMessage: (message: string, image?: string) => void
  onClearChat?: () => void
  isProcessing: boolean
  activeAgent: string | null
  language?: Language
}

export default function ChatPanel({
  messages, onSendMessage, onClearChat, isProcessing, activeAgent, language = 'es',
}: ChatPanelProps) {
  const t = getTranslations(language)
  const [input, setInput] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if ((!input.trim() && !pendingImage) || isProcessing) return
    onSendMessage(input.trim() || 'Analyze this image', pendingImage || undefined)
    setInput(''); setPendingImage(null); setImagePreview(null)
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !file.type.startsWith('image/')) return
    
    // Compress image to max 800KB to avoid model input limits
    const maxSize = 800 * 1024 // 800KB
    const reader = new FileReader()
    reader.onload = () => {
      const b64 = reader.result as string
      if (b64.length > maxSize) {
        // Compress using canvas
        const img = new Image()
        img.onload = () => {
          const canvas = document.createElement('canvas')
          let width = img.width
          let height = img.height
          // Scale down to max 1024px on longest side
          const maxDim = 1024
          if (width > maxDim || height > maxDim) {
            if (width > height) { height = (height * maxDim) / width; width = maxDim }
            else { width = (width * maxDim) / height; height = maxDim }
          }
          canvas.width = width
          canvas.height = height
          const ctx = canvas.getContext('2d')
          ctx?.drawImage(img, 0, 0, width, height)
          const compressed = canvas.toDataURL('image/jpeg', 0.7)
          setPendingImage(compressed)
          setImagePreview(compressed)
        }
        img.src = b64
      } else {
        setPendingImage(b64)
        setImagePreview(b64)
      }
    }
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  const toggleVoice = () => {
    const SpeechAPI = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    if (!SpeechAPI) return
    if (isListening) { setIsListening(false); return }
    try {
      const recognition = new SpeechAPI()
      recognition.lang = language === 'zh' ? 'zh-CN' : language
      recognition.continuous = false; recognition.interimResults = true
      recognition.onstart = () => setIsListening(true)
      recognition.onresult = (event: any) => {
        const last = event.results.length - 1
        const transcript = event.results[last][0].transcript
        setInput(transcript)
        if (event.results[last].isFinal && transcript.trim()) {
          setIsListening(false); onSendMessage(transcript.trim()); setInput('')
        }
      }
      recognition.onerror = () => setIsListening(false)
      recognition.onend = () => setIsListening(false)
      recognition.start()
    } catch { setIsListening(false) }
  }

  const getAgentColor = (agent?: string) => {
    const colors: Record<string, string> = {
      energia: 'text-yellow-400', logistica: 'text-blue-400', soporte: 'text-green-400',
      visual: 'text-purple-400', analytics: 'text-cyan-400', society: 'text-rose-400',
    }
    return colors[agent || ''] || 'text-slate-400'
  }

  return (
    <div className="flex flex-col h-full bg-slate-900/50 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot size={20} className="text-disa-secondary" />
          <span className="font-medium text-white">{t.copilotTitle}</span>
          {activeAgent && (
            <span className={`text-xs px-2 py-0.5 rounded-full bg-slate-800 ${getAgentColor(activeAgent)}`}>
              {getAgentLabel(activeAgent, language)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Multi-Agent • LangGraph • MCP • Qwen Cloud</span>
          {messages.length > 0 && onClearChat && (
            <button onClick={onClearChat} className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-slate-700" title={t.newConversation}>
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-disa-primary/20 rounded-full flex items-center justify-center mb-4">
              <Bot size={32} className="text-disa-secondary" />
            </div>
            <h3 className="text-white font-medium text-lg mb-2">{t.welcomeTitle}</h3>
            <p className="text-slate-400 text-sm max-w-md">{t.welcomeSubtitle}</p>
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              {[t.suggestBill, t.suggestPackages, t.suggestRecharge, t.suggestEarnings, t.suggestGrow].map((s) => (
                <button key={s} onClick={() => onSendMessage(s)}
                  className="text-xs px-3 py-1.5 rounded-full bg-slate-800 border border-slate-600 text-slate-300 hover:border-disa-secondary hover:text-white transition-colors">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-agent'}>
              {msg.role === 'agent' && msg.agent && (
                <div className={`text-xs font-medium mb-1 ${getAgentColor(msg.agent)}`}>
                  {getAgentLabel(msg.agent, language)}
                </div>
              )}
              {msg.image && <div className="text-xs text-slate-400 mb-1">📎 {t.imageAttached}</div>}
              <div className="text-sm text-slate-200 prose prose-invert prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-headings:text-slate-100 prose-strong:text-white">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {msg.tools && msg.tools.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {msg.tools.map((tool) => (
                    <span key={tool} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">🔧 {tool}</span>
                  ))}
                </div>
              )}
              <span className="text-[10px] text-slate-500 mt-1 block">
                {new Date(msg.timestamp).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="chat-bubble-agent flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-disa-secondary" />
              <span className="text-sm text-slate-400">{t.processing}</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="px-4 py-2 border-t border-slate-700 flex items-center gap-2">
          <img src={imagePreview} alt="" className="w-16 h-16 object-cover rounded-lg border border-slate-600" />
          <span className="text-xs text-slate-400">{t.imageAttached}</span>
          <button onClick={() => { setPendingImage(null); setImagePreview(null) }} className="p-1 rounded text-slate-400 hover:text-red-400"><X size={14} /></button>
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-slate-700">
        <div className="flex items-center gap-2">
          <button type="button" onClick={toggleVoice}
            className={`p-2.5 rounded-lg transition-colors ${isListening ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'}`}>
            {isListening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <button type="button" onClick={() => fileInputRef.current?.click()}
            className="p-2.5 rounded-lg bg-slate-800 text-slate-400 hover:text-purple-400 border border-slate-700" title={t.uploadImage}>
            <ImagePlus size={18} />
          </button>
          <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)}
            placeholder={isListening ? t.listening : t.placeholder} disabled={isProcessing}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-disa-secondary disabled:opacity-50" />
          <button type="submit" disabled={(!input.trim() && !pendingImage) || isProcessing}
            className="p-2.5 bg-disa-primary rounded-lg text-white hover:bg-disa-secondary disabled:opacity-30 disabled:cursor-not-allowed">
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}
