// Next.js config — TalentChart frontend
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // cho Docker deploy
  reactStrictMode: true,

  // ★ Chuyển tiếp /api/* vào backend (same-origin — không cần CORS, không cần
  // reverse-proxy tách route). Dev: localhost:8003; Docker: talentchart-backend:8003
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL ?? 'http://localhost:8003';
    return [
      { source: '/api/:path*', destination: `${backend}/api/:path*` },
      { source: '/health', destination: `${backend}/health` },
    ];
  },
};

export default nextConfig;
