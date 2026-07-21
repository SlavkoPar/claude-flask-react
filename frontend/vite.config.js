import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react' // Use your framework plugin (vue, svelte, etc.)
import { resolve } from 'path'

export default defineConfig(({ command, mode }) => {
  // Check if we are compiling for production
  const isProduction = mode === 'production'

  return {
    plugins: [react()],
    server: {
      proxy: isProduction ? {
        '/api': 'https://knowledge-i4sn.onrender.com',
        '/auth': 'https://knowledge-i4sn.onrender.com',
      } :
        {
          '/api': 'http://localhost:5000',
          '/auth': 'http://localhost:5000',
        },

      // Public base path for production assets
      base: isProduction ? 'https://claude-flask-react-1.onrender.com' : '/',

      resolve: {
        alias: {
          '@': resolve(__dirname, './src'),
        },
      },

      build: {
        // Set the output directory for the compiled assets
        outDir: 'dist',
        css: {
          preprocessorOptions: {
            scss: {
              quietDeps: true,
              silenceDeprecations: ['color-functions', 'import', 'global-builtin'],
            },
          },
        },

        // Specify target environment (modern browsers supporting ES Modules)
        target: 'esnext',

        // Generate a manifest.json file for backend integration
        manifest: true,

        // Control sourcemap generation (false saves space, 'hidden' hides comments)
        sourcemap: false,

        // Adjust chunk size warning limit (in kB)
        chunkSizeWarningLimit: 1000,

        // Advanced Rollup bundling options
        rollupOptions: {
          input: {
            main: resolve(__dirname, 'index.html'),
          },
          output: {
            // Keep asset names predictable and cache-safe using hashes
            output: {
              entryFileNames: `assets/[name].js`,
              chunkFileNames: `assets/[name].js`,
              assetFileNames: `assets/[name].[ext]`
            },

            // Split large dependencies into separate chunks
            manualChunks(id) {
              if (id.includes('node_modules')) {
                // Create separate vendor chunk for react ecosystem
                if (id.includes('react')) {
                  return 'vendor-react'
                }
                // Catch-all for other external modules
                return 'vendor'
              }
            },
          },
        },

        // Drop console and debugger statements to optimize file sizes
        minify: 'esbuild',
        esbuild: {
          drop: isProduction ? ['console', 'debugger'] : [],
        },
      },
    }
  }
})
