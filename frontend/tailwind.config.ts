import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        'primary-light': '#3b82f6',
        accent: '#f59e42',
        background: '#0f172a', // Dark theme background
        'sidebar-bg': 'rgba(30, 41, 59, 0.8)',
        'card-bg': 'rgba(30, 41, 59, 0.6)',
        'card-glass': 'rgba(51, 65, 85, 0.8)',
        active: '#22c55e',
        processing: '#f59e42',
        idle: '#94a3b8',
        border: '#334155',
        text: '#f8fafc',
        muted: '#94a3b8',
      },
      fontFamily: {
        inter: ['Inter', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        'xl': '18px',
        '2xl': '28px',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
      },
    },
  },
  plugins: [],
}

export default config