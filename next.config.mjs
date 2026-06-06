/* global process */

/** @type {import('next').NextConfig} */
const isDev = process.env.NODE_ENV !== "production";

const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // CI/QA runs `npm run lint` explicitly. Next 15's build-time detector does
    // not reliably recognize flat ESLint configs, so keep build focused on the
    // production bundle after the lint gate has passed.
    ignoreDuringBuilds: true,
  },
  async headers() {
    const securityHeaders = [
      {
        key: "Content-Security-Policy",
        value:
          `default-src 'self'; script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'${isDev ? " ws://127.0.0.1:* ws://localhost:*" : ""}; font-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; upgrade-insecure-requests`,
      },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "Permissions-Policy", value: "camera=(self), microphone=(self), geolocation=()" },
      { key: "X-Frame-Options", value: "DENY" },
    ];
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
      {
        source: "/api/(.*)",
        headers: [
          ...securityHeaders,
          { key: "Cache-Control", value: "no-store" },
        ],
      },
      {
        // Allow the service worker to control the whole app scope.
        source: "/sw.js",
        headers: [
          ...securityHeaders,
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },
};

export default nextConfig;
