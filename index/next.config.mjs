import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // De site leest manifests buiten zijn eigen map; dit voorkomt monorepo-warnings.
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
