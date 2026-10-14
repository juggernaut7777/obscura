/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable source maps in production to cut memory and bundle size
  productionBrowserSourceMaps: false,
  // Aggressive asset caching for static images and product catalogs
  async headers() {
    return [
      {
        source: '/products/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
