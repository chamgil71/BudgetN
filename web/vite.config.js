import { defineConfig } from 'vite'
import { resolve } from 'path'
import { cpSync, existsSync } from 'fs'

// Non-module scripts (js/, css/, data/) can't be bundled by Vite — copy them verbatim to dist/
function copyStaticDirs() {
  return {
    name: 'copy-static-dirs',
    writeBundle(options) {
      const outDir = options.dir || resolve(__dirname, 'dist')
      for (const dir of ['js', 'css', 'data']) {
        const src = resolve(__dirname, dir)
        const dest = resolve(outDir, dir)
        if (existsSync(src)) cpSync(src, dest, { recursive: true })
      }
    }
  }
}

export default defineConfig({
  base: '/',
  plugins: [copyStaticDirs()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html')
      }
    }
  }
})