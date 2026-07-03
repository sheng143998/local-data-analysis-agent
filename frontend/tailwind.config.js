/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        graphite: '#111827',
        ink: '#0f172a',
        cyanline: '#22d3ee',
        mint: '#10b981',
        amberline: '#f59e0b',
      },
      boxShadow: {
        cockpit: '0 18px 50px rgba(15, 23, 42, 0.14)',
        line: 'inset 0 0 0 1px rgba(148, 163, 184, 0.22)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Arial'],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
