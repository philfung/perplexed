/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {


    extend: {
      animation: {
        'pulse': 'pulseAnimation 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
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
        'header-height': '70px',
        '1/8-screen': '12.5vh'
      },
      width: {
      'width-percent-45': '45%'
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

