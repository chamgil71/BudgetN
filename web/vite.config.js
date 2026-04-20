import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  // Vercel은 보통 루트('/') 경로를 사용합니다. 
  // 특별히 주소 뒤에 /BudgetN/을 붙여서 접속해야 하는 상황이 아니라면 '/'로 수정하세요.
  base: '/', 
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        login: resolve(__dirname, 'login.html') // Vite가 login.html도 빌드하도록 명시
      }
    }
  }
})