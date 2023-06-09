/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./webapp/**/*.{html,j2}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

