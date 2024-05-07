/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {


    extend: {
      boxShadow: {
        'outline': '0 0 0 3px rgba(66, 153, 225, 0.5)',
      },
      colors: {
        'pp-text-white': '#E8E8E6',
        'pp-text-grey': '#8C9090',
        'pp-bg-dark-grey': 'rgba(25,26,26,1.0)',
        'pp-bg-light-grey': 'rgba(32,34,34,1.0)',
        'pp-border-grey':'rgba(61, 63, 64, 1.0)',
        'pp-light-blue': '#1fb8cd',
        'pp-button-grey': '#2F302F'
      },
      fontFamily: {
        'fkgrneue': ['FKGRNeue', 'sans-serif'],
        'fkgr': ['FKGR', 'sans-serif'],
        'bmono': ['BMono', 'monospace'],
      },
      fontSize: {
        '15': '15px'
      },
      spacing: {
        'header-height': '100px',
      }
    },
  },
  variants: {
    extend: {
      boxShadow: ['focus'],
    },
  },
  plugins: [],
}

