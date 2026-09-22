
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  experimental: {
    optimizePackageImports: ["framer-motion", "lightweight-charts", "lucide-react", "recharts"],
  },
};

export default nextConfig;
