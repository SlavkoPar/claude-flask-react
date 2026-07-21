
/*
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name].js`,
        chunkFileNames: `assets/[name].js`,
        assetFileNames: `assets/[name].[ext]`
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true,
        silenceDeprecations: ['global-builtin', 'import'],
      },
    },
  },
});
*/

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react'; // Or your framework plugin (vue, svelte, etc.)
import path from 'path';

export default defineConfig(({ command, mode }) => {
  // Load env variables based on the current mode (development, production, etc.)
  // The third argument '' loads all variables instead of just those prefixed with VITE_
  const env = loadEnv(mode, process.cwd(), '');

  // Shared configuration options for both dev and prod
  const sharedConfig = {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          quietDeps: true,
          silenceDeprecations: ['global-builtin', 'import'],
        },
      },
    },
  };

  if (command === 'production') {
    return {
      ...sharedConfig,
      server: {
        port: 5173, // Specify the port for development server
        open: true, // Auto-open browser
        proxy: {
          '/api': {
            target: env.VITE_API_PRODUCTION_URL || 'http://localhost:5000',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
          },
          '/auth': {
            target: env.VITE_API_PRODUCTION_URL || 'http://localhost:5000',
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/auth/, ''),
          },
        },
      },
    };
  }

  // Production specific configuration (command === 'build')
  return {
    ...sharedConfig,
    base: './', // Changes public path for production builds if needed
    build: {
      outDir: 'dist',
      sourcemap: false, // Turn off sourcemaps to save build size/security
      minify: 'esbuild', // Faster minification
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          entryFileNames: `assets/[name].js`,
          chunkFileNames: `assets/[name].js`,
          assetFileNames: `assets/[name].[ext]`
        }
      }
    },
  };
});


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
        '/api': 'http://localhost:5000',
        '/auth': 'http://localhost:5000',
      } :
      {
        '/api': 'https://knowledge-i4sn.onrender.com',
        '/auth': 'https://knowledge-i4sn.onrender.com',
      } ,

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
  })
