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

const SVETLANA_AVATAR_ASSET = '/static/svetlana/svetlana-office.jpg'

/**
 * Основной аватар Светланы — локальный статичный брендовый портрет.
 * Изображение хранится отдельно от компонента, поэтому его можно заменить
 * без изменения UI-кода.
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
      className={`${sizeClass[size]} ${className} relative flex items-end justify-center overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_50%_25%,rgba(52,211,153,.18),transparent_55%),linear-gradient(145deg,#f8fafc,#e2e8f0)] shadow-2xl`}
      aria-label="Светлана"
      data-svetlana-avatar="local"
    >
      {!error && (
        <img
          src={SVETLANA_AVATAR_ASSET}
          alt="Светлана — помощник «Мира Самозанятых»"
          className={`h-full w-full object-contain object-bottom transition duration-700 ${loaded ? 'opacity-100' : 'opacity-0'} ${interactive ? 'animate-[svetlanaFloat_4s_ease-in-out_infinite]' : ''}`}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          draggable={false}
        />
      )}
      {(!loaded || error) && (
        <div className="absolute inset-0 flex items-center justify-center p-4 text-center text-slate-600">
          {error ? 'Аватар Светланы недоступен' : 'Светлана загружается…'}
        </div>
      )}
      <div className="absolute bottom-2 right-2 flex items-center gap-1.5 rounded-full border border-slate-900/10 bg-white/80 px-2 py-1 text-[9px] font-bold text-emerald-700 backdrop-blur">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> OFFLINE
      </div>
    </div>
  )
}

export function commandSvetlana(_iframe: HTMLIFrameElement | null, _payload: Record<string, unknown>) {
  // Compatibility no-op: the primary avatar is intentionally static.
}
