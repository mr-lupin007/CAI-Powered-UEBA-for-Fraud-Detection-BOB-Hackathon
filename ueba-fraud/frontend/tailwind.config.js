/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",   // <— include jsx/tsx if you use them
  ],
  theme: { extend: {} },
  plugins: [],
};
