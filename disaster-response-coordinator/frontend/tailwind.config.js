/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0a0f1e',
          800: '#0d1427',
          700: '#111c35',
          600: '#162142',
          500: '#1e2d54',
        }
      }
    },
  },
  plugins: [],
}
