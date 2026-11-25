/* Build: tailwindcss -c tailwind.config.cjs -i css/src.css -o css/site.css --minify
   (Tailwind v3; replaces the Play CDN script so the live site ships static CSS.) */
module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Barlow', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        block: ['Anton', 'Impact', 'sans-serif'],
        brush: ['Knewave', 'Impact', 'cursive'],
      },
      colors: {
        ink: '#09090c', deck: '#13131a', line: '#2a2a35',
        gold: '#f5b90f', neon: '#2f8cff', heat: '#ff3b30', chalk: '#f4f1ea',
      },
    },
  },
}
