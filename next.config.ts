import type { NextConfig } from "next";

// For GitHub Pages: the site is served from https://username.github.io/WildAtlas/
// so we need a basePath of /WildAtlas in production. In dev, serve from /.
const isProd = process.env.NODE_ENV === "production";
const repoName = "WildAtlas"; // GitHub repo name

const nextConfig: NextConfig = {
  // Static export for GitHub Pages (no server needed)
  output: isProd ? "export" : "standalone",
  // Required for static export: disable server-side image optimization
  images: { unoptimized: true },
  // GitHub Pages serves from /WildAtlas/ — set basePath in production only
  basePath: isProd ? `/${repoName}` : "",
  assetPrefix: isProd ? `/${repoName}/` : "",
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  // Trailing slashes for GitHub Pages compatibility
  trailingSlash: true,
};

export default nextConfig;
