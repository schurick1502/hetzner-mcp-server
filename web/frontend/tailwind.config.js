/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        hetzner: {
          red: '#D50C2D',
          blue: '#0A1E42',
        }
      }
    },
  },
  plugins: [],
}
