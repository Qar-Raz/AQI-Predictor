/** @type {import('next').NextConfig} */
const nextConfig = {
    // This rewrite configuration is the "bridge" for local development
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*', // Proxy to your FastAPI server
        },
      ]
    },
  };
  
  export default nextConfig;