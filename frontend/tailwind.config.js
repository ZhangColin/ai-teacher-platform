/** @type {import('tailwindcss').Config} */
import typography from '@tailwindcss/typography';

export default {
  // 注意：这里要把 ts, tsx 也加上
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}