/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Wine Colors
        burgundy: {
          50: '#fdf2f4',
          100: '#fce7eb',
          200: '#f9d0d9',
          300: '#f4a9ba',
          400: '#ec7695',
          500: '#e04d73',
          600: '#cc2d5a',
          700: '#ab2049',
          800: '#8f1d40',
          900: '#722F37', // Main burgundy
          950: '#4a0d1c',
        },
        gold: {
          50: '#fdfbeb',
          100: '#faf5c7',
          200: '#f6e992',
          300: '#f0d654',
          400: '#e9c026',
          500: '#D4AF37', // Main gold
          600: '#b38518',
          700: '#8f6216',
          800: '#774e1a',
          900: '#65411c',
          950: '#3a210c',
        },
        cream: {
          50: '#FFF8E7', // Main cream
          100: '#fef3d7',
          200: '#fde4af',
          300: '#fbd07d',
          400: '#f8b349',
          500: '#f49620',
          600: '#e57a14',
          700: '#be5c12',
          800: '#974917',
          900: '#7a3d17',
          950: '#421e09',
        },
        wine: {
          red: '#722F37',
          white: '#F5E6D3',
          rose: '#E8B4B8',
          sparkling: '#F0E68C',
        }
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['Lato', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'wine-pattern': "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23722F37' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      boxShadow: {
        'wine': '0 4px 14px 0 rgba(114, 47, 55, 0.2)',
        'gold': '0 4px 14px 0 rgba(212, 175, 55, 0.3)',
      }
    },
  },
  plugins: [],
}

