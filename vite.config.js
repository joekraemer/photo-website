import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Served from the project page https://joekraemer.github.io/photo-website/, so
// every asset and route lives under /photo-website/ (import.meta.env.BASE_URL).
// Output stays in build/, where the Pages workflow uploads it from.
export default defineConfig({
    base: '/photo-website/',
    plugins: [react()],
    build: { outDir: 'build' },
    test: { globals: true, environment: 'node' },
});
