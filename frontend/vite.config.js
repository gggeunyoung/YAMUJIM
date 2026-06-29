import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 개발 서버는 기본 5173 포트(백엔드 CORS 화이트리스트에 등록됨).
// '/api' 요청은 Django(runserver 8000)로 프록시한다.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // 추천 생성은 LLM 호출로 ~24초+ 걸리므로 타임아웃을 넉넉히.
        timeout: 180000,
        proxyTimeout: 180000,
      },
    },
  },
})
