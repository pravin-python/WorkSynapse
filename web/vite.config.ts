import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        host: '0.0.0.0',
        allowedHosts: ["localhost:5173", "localhost:8000", "10.0.101.117:8000", "10.0.101.117:5173"],
        proxy: {
            '/api': {
                target: 'http://10.0.101.117:8000',
                changeOrigin: true,
                secure: false,
            }
        }
    }
})
