import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// scripts/derive.mjs reads ../Records and ../test_data at build time and writes src/generated/derived.json,
// so every number on the page is generated from repo files, never typed.
// The base is a subpath because the capture app in frontend/ keeps the Pages root.
export default defineConfig({
  base: '/drawing-modality-test/dashboard/',
  plugins: [react()],
});
