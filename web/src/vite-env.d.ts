/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string
    readonly VITE_API_KEY: string
    readonly VITE_SECRET_KEY: string
    readonly VITE_WS_URL: string
    readonly VITE_APP_NAME: string
    readonly VITE_APP_VERSION: string
    readonly VITE_ENABLE_AI_AGENTS: string
    readonly VITE_ENABLE_CHAT: string
    readonly VITE_ENABLE_TIME_TRACKING: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
