/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f1117',
        surface: '#1e212b',
        primary: '#3b82f6',
        primaryHover: '#2563eb',
        textMain: '#f8fafc',
        textMuted: '#94a3b8',
        border: '#334155'
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
