// frontend/src/components/Logo.tsx

interface Props {
  size?: number;
  className?: string;
}

export default function Logo({ size = 72, className = "" }: Props) {
  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
      aria-label="DisasterIQ logo"
    >
      <svg
        viewBox="0 0 120 120"
        width={size}
        height={size}
        role="img"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="badgeBg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="55%" stopColor="#050816" />
            <stop offset="100%" stopColor="#020617" />
          </linearGradient>

          <linearGradient id="dStroke" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f8fafc" />
            <stop offset="100%" stopColor="#cbd5e1" />
          </linearGradient>

          <linearGradient id="qStroke" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>

          <linearGradient id="landGreen" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#6ee7b7" />
            <stop offset="100%" stopColor="#22c55e" />
          </linearGradient>

          <linearGradient id="floodBrown" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#d6a06a" />
            <stop offset="100%" stopColor="#8b5e34" />
          </linearGradient>

          <linearGradient id="waterBlue" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#60a5fa" />
            <stop offset="100%" stopColor="#1d4ed8" />
          </linearGradient>

          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow
              dx="0"
              dy="8"
              stdDeviation="7"
              floodColor="#000000"
              floodOpacity="0.45"
            />
          </filter>

          <filter id="orangeGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow
              dx="0"
              dy="0"
              stdDeviation="4"
              floodColor="#f97316"
              floodOpacity="0.35"
            />
          </filter>

          <clipPath id="lensClip">
            <circle cx="56" cy="61" r="24" />
          </clipPath>
        </defs>

        <g filter="url(#softShadow)">
          <rect
            x="8"
            y="8"
            width="82"
            height="82"
            rx="18"
            fill="url(#badgeBg)"
            stroke="rgba(96,165,250,0.18)"
            strokeWidth="2"
          />

          <rect
            x="10"
            y="10"
            width="78"
            height="78"
            rx="16"
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1.5"
          />
        </g>

        <path
          d="M30 24h19c19 0 34 15 34 34s-15 34-34 34H30z"
          fill="none"
          stroke="url(#dStroke)"
          strokeWidth="10"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        <path
          d="M43 35h6c13 0 23 10 23 23s-10 23-23 23h-6z"
          fill="rgba(255,255,255,0.04)"
        />

        <g clipPath="url(#lensClip)">
          <rect x="32" y="37" width="48" height="48" fill="#0b1220" />

          <polygon points="32,37 80,37 80,56 50,56" fill="url(#landGreen)" />
          <polygon
            points="32,49 50,56 80,56 80,85 32,85"
            fill="url(#floodBrown)"
          />

          <path
            d="M32 45 C42 48, 47 53, 53 57 C60 61, 69 66, 80 69 L80 85 L32 85 Z"
            fill="url(#waterBlue)"
            opacity="0.88"
          />

          <g opacity="0.22" stroke="#e2e8f0" strokeWidth="0.7">
            <line x1="32" y1="49" x2="80" y2="49" />
            <line x1="32" y1="61" x2="80" y2="61" />
            <line x1="32" y1="73" x2="80" y2="73" />
            <line x1="44" y1="37" x2="44" y2="85" />
            <line x1="56" y1="37" x2="56" y2="85" />
            <line x1="68" y1="37" x2="68" y2="85" />
          </g>

          <g opacity="0.92">
            <rect
              x="38"
              y="43"
              width="13"
              height="13"
              rx="2.5"
              fill="#22c55e"
              stroke="#f8fafc"
              strokeWidth="0.8"
            />
            <rect
              x="53"
              y="43"
              width="13"
              height="13"
              rx="2.5"
              fill="#facc15"
              stroke="#f8fafc"
              strokeWidth="0.8"
            />
            <rect
              x="38"
              y="58"
              width="13"
              height="13"
              rx="2.5"
              fill="#fb923c"
              stroke="#f8fafc"
              strokeWidth="0.8"
            />
            <rect
              x="53"
              y="58"
              width="13"
              height="13"
              rx="2.5"
              fill="#ef4444"
              stroke="#f8fafc"
              strokeWidth="0.8"
            />
          </g>

          <g fill="#111827" opacity="0.5">
            <rect x="66" y="62" width="5" height="5" rx="1" />
            <rect x="70" y="51" width="4" height="4" rx="1" />
            <rect x="44" y="72" width="5" height="5" rx="1" />
          </g>
        </g>

        <g filter="url(#orangeGlow)">
          <circle
            cx="56"
            cy="61"
            r="30"
            fill="none"
            stroke="url(#qStroke)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="164 34"
            transform="rotate(-36 56 61)"
          />
        </g>

        <path
          d="M75 81 L92 98"
          stroke="url(#qStroke)"
          strokeWidth="8"
          strokeLinecap="round"
        />

        <circle
          cx="56"
          cy="61"
          r="24.5"
          fill="none"
          stroke="rgba(255,255,255,0.22)"
          strokeWidth="1.5"
        />
      </svg>
    </div>
  );
}
