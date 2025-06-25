import type { Config } from 'tailwindcss'

export default <Config>{
  content: [
    './components/**/*.{vue,js,ts}',
    './pages/**/*.{vue,js,ts}'
  ],
  theme: {
    extend: {}
  },
  plugins: []
}
