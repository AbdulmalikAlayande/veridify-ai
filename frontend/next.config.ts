import type { NextConfig } from "next"

// When NEXT_PUBLIC_API_BASE_URL is a relative path like "/api/proxy", the browser
// hits the Next.js server (same-origin → no CORS) and we forward the request to
// API_PROXY_TARGET on the server side. Set API_PROXY_TARGET in .env.local; for
// production deploys, set it in the host's environment.
const proxyTarget = process.env.API_PROXY_TARGET?.replace(/\/+$/, "")

const nextConfig: NextConfig = {
  async rewrites() {
    if (!proxyTarget) {
      return []
    }

    return [
      {
        source: "/api/proxy/:path*",
        destination: `${proxyTarget}/:path*`,
      },
    ]
  },
}

export default nextConfig
