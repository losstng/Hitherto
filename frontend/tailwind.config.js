module.exports = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx}',         // <- REQUIRED for App Router
    './src/components/**/*.{js,ts,jsx,tsx}',  // <- Your components
    './src/styles/**/*.css',                  // <- Optional but smart
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

