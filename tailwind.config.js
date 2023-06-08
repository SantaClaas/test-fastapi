/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./webapp/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
  ],
}

