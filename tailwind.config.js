/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./wApp/**/*.{html,j2}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

