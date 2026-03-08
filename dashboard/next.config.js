/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_COLLECTOR_URL:
      process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8001",
  },
};

module.exports = nextConfig;
