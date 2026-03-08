/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          primary: 'rgb(10 10 15 / <alpha-value>)',
          secondary: 'rgb(18 18 26 / <alpha-value>)',
          card: 'rgb(26 26 46 / <alpha-value>)',
          'card-hover': 'rgb(31 31 53 / <alpha-value>)',
          elevated: 'rgb(37 37 64 / <alpha-value>)',
          border: 'rgb(42 42 69 / <alpha-value>)',
          'border-bright': 'rgb(58 58 92 / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
