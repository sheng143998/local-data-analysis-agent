/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: '#C96442',
          50: '#FAF1EC',
          100: '#F5E8E2',
          200: '#EBD0C3',
          300: '#DFB3A0',
          400: '#D48B6C',
          500: '#C96442',
          600: '#B55535',
          700: '#9A4930',
          800: '#7C3B28',
          900: '#5F2E20',
        },
        success: {
          DEFAULT: '#7D9B76',
          soft: '#EEF3EC',
        },
        warning: {
          DEFAULT: '#D4A27F',
          soft: '#F8EFE6',
        },
        danger: {
          DEFAULT: '#C14C3D',
          soft: '#F8E9E6',
        },
        paper: '#FAF9F5',
      },
      boxShadow: {
        soft: '0 1px 3px rgba(28, 25, 23, 0.06), 0 4px 16px rgba(28, 25, 23, 0.04)',
        lift: '0 2px 6px rgba(28, 25, 23, 0.08), 0 10px 28px rgba(28, 25, 23, 0.08)',
      },
      fontFamily: {
        sans: ['PingFang SC', 'Microsoft YaHei', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      transitionTimingFunction: {
        swift: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
      },
    },
  },
  plugins: [],
};
