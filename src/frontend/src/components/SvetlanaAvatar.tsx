import { useEffect, useRef, useState } from 'react'

type Props = {
  size?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  className?: string
}

export default function SvetlanaAvatar({ size = 'md', interactive = false, className = '' }: Props) {
  const ref = useRef<HTMLIFrameElement>(null)
  const [runtimeError, setRuntimeError] = useState(false)
  const dims = size === 'lg' ? 'h-72 w-full' : size === 'sm' ? 'h-12 w-12' : 'h-24 w-24'

  useEffect(() => {
    const onMessage = (e: MessageEvent) => {
      if (e.source !== ref.current?.contentWindow) return
      if (e.data?.type === 'svetlana.ready') {
        setRuntimeError(false)
        if (interactive) {
          ref.current?.contentWindow?.postMessage(
            { type: 'svetlana.emotion', name: 'smile', duration: 1800 },
            window.location.origin,
          )
        }
      }
      if (e.data?.type === 'svetlana.error') setRuntimeError(true)
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [interactive])

  return (
    <div
      className={`${dims} ${className} relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-lg`}
      aria-label="Светлана"
    >
      <iframe
        ref={ref}
        title="Светлана — 3D AI-ассистент"
        src="/svetlana/index.html"
        className="h-full w-full border-0"
        loading={size === 'sm' ? 'lazy' : 'eager'}
        allow="autoplay; fullscreen"
      />
      {runtimeError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-1 bg-slate-950 p-3 text-center text-white">
          <span className="text-sm font-bold">Светлана</span>
          <span className="text-[10px] text-white/60">локальный аватар недоступен</span>
        </div>
      )}
      <span className="absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" title="Локальный runtime" />
    </div>
  )
}

export function commandSvetlana(iframe: HTMLIFrameElement | null, payload: Record<string, unknown>) {
  iframe?.contentWindow?.postMessage({ type: 'svetlana.command', payload }, window.location.origin)
}
