/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./wappstore/**/*.{html,j2}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

