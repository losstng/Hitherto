module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',         // <- REQUIRED for App Router
    './components/**/*.{js,ts,jsx,tsx}',  // <- Your components
    './styles/**/*.{css}',                // <- Optional but smart
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};