
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

  // Development specific configuration
  if (command === 'serve') {
    return {
      ...sharedConfig,
      server: {
        port: 5173, // Specify the port for development server
        open: true, // Auto-open browser
        proxy: {
          '/api': {
            target: env.VITE_API_DEV_URL || 'http://localhost:5000',
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

