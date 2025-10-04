/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
  webpack: (config) => {
    // Suppress webpack warnings about path casing on Windows
    config.infrastructureLogging = {
      level: 'error',
    }
    
    return config
  },
}

module.exports = nextConfig
