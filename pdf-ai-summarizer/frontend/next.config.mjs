/** @type {import('next').NextConfig} */
// output: 'standalone' de Docker build ra image gon (chi copy .next/standalone),
// khong anh huong `next dev`/`next build` khi chay local binh thuong.
const nextConfig = {
  output: 'standalone',
};

export default nextConfig;
