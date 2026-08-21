import { useEffect, useRef, useState } from 'react'

type Props = {
  size?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  className?: string
}

export default function SvetlanaAvatar({ size = 'md', interactive = false, className = '' }: Props) {
  const ref = useRef<HTMLIFrameElement>(null)
  const [runtimeError, setRuntimeError] = useState(false)
  const dims = size === 'lg' ? 'h-64 w-full' : size === 'sm' ? 'h-12 w-12' : 'h-24 w-24'

  useEffect(() => {
    if (!interactive) return
    const onMessage = (e: MessageEvent) => {
      if (e.source !== ref.current?.contentWindow) return
      if (e.data?.type === 'svetlana.ready') {
        setRuntimeError(false)
        ref.current?.contentWindow?.postMessage(
          { type: 'svetlana.emotion', name: 'smile', duration: 1800 },
          window.location.origin,
        )
      }
      if (e.data?.type === 'svetlana.error') setRuntimeError(true)
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [interactive])

  return (
    <div className={`${dims} ${className} relative overflow-hidden rounded-2xl border border-slate-200 bg-[#10131a] shadow-lg`} aria-label="Светлана">
      {interactive ? (
        <>
          <iframe
            ref={ref}
            title="Светлана — 3D AI-ассистент"
            src="/svetlana/index.html"
            className="h-full w-full border-0"
            loading="eager"
            allow="autoplay; fullscreen"
          />
          {runtimeError && (
            <div className="absolute inset-0 flex items-center justify-center bg-[#10131a] p-4 text-center text-xs text-white/70">
              Светлана не смогла загрузить 3D-модель
            </div>
          )}
        </>
      ) : (
        <div className="flex h-full w-full items-center justify-center bg-[radial-gradient(circle_at_35%_20%,#fff7ed_0,#fed7aa_28%,#f97316_62%,#9a3412_100%)]">
          <div className="flex h-[72%] w-[72%] items-center justify-center rounded-full border border-white/40 bg-white/15 text-2xl font-black text-white shadow-inner backdrop-blur-sm">
            С
          </div>
        </div>
      )}
      <span className="absolute bottom-1 right-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" />
    </div>
  )
}

export function commandSvetlana(iframe: HTMLIFrameElement | null, payload: Record<string, unknown>) {
  iframe?.contentWindow?.postMessage({ type: 'svetlana.command', payload }, window.location.origin)
}
