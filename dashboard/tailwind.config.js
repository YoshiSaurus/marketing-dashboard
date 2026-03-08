/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          primary: '#0a0a0f',
          secondary: '#12121a',
          card: '#1a1a2e',
          'card-hover': '#1f1f35',
          elevated: '#252540',
          border: '#2a2a45',
          'border-bright': '#3a3a5c',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
