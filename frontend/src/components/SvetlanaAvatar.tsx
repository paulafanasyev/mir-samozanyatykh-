import { useEffect, useState } from 'react'

type Props = {
  size?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  className?: string
}

const sizeClass = {
  sm: 'h-12 w-12',
  md: 'h-24 w-24',
  lg: 'h-80 w-full',
} as const

/**
 * Светлана всегда отображает именно локальный брендовый портрет из репозитория.
 * 3D-модель остаётся доступной на отдельной странице, но основной UI не зависит
 * от iframe/WebGL: аватар не исчезает при проблемах браузера или WebGL.
 */
export default function SvetlanaAvatar({ size = 'md', interactive = false, className = '' }: Props) {
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoaded(false)
    setError(false)
  }, [size])

  return (
    <div
      className={`${sizeClass[size]} ${className} relative overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_50%_25%,rgba(251,146,60,.25),transparent_55%),linear-gradient(145deg,#0f172a,#020617)] shadow-2xl`}
      aria-label="Светлана"
      data-svetlana-avatar="local"
    >
      {!error && (
        <img
          src="/static/svetlana/base.png"
          alt="Светлана — помощник «Мира Самозанятых»"
          className={`h-full w-full object-cover object-top transition duration-700 ${loaded ? 'opacity-100' : 'opacity-0'} ${interactive ? 'animate-[svetlanaFloat_4s_ease-in-out_infinite]' : ''}`}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          draggable={false}
        />
      )}
      {(!loaded || error) && (
        <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-white/80">
          {error ? 'Аватар Светланы недоступен' : 'Светлана загружается…'}
        </div>
      )}
      <div className="absolute bottom-2 right-2 flex items-center gap-1.5 rounded-full border border-white/10 bg-slate-950/75 px-2 py-1 text-[9px] font-bold text-emerald-300 backdrop-blur">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> OFFLINE
      </div>
    </div>
  )
}

export function commandSvetlana(_iframe: HTMLIFrameElement | null, _payload: Record<string, unknown>) {
  // The primary avatar is now rendered directly from the versioned local asset.
  // Kept as a compatibility no-op for existing callers.
}
