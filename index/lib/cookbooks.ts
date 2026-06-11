import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";

export type Cookbook = {
  slug: string;
  name: string;
  description: string;
  type: "app" | "workflow" | "notebook";
  runtime: "node" | "python-serverless" | "python-server" | "notebook" | "none";
  stack: string[];
  owner: string;
  deploy: boolean;
  url?: string;
  tags: string[];
};

const COOKBOOKS_DIR = path.join(process.cwd(), "..", "cookbooks");

export function getCookbooks(): Cookbook[] {
  if (!fs.existsSync(COOKBOOKS_DIR)) return [];
  return fs
    .readdirSync(COOKBOOKS_DIR, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const manifestPath = path.join(COOKBOOKS_DIR, entry.name, "cookbook.yaml");
      if (!fs.existsSync(manifestPath)) return null;
      const manifest = parse(fs.readFileSync(manifestPath, "utf8")) as Cookbook;
      return { ...manifest, tags: manifest.tags ?? [], stack: manifest.stack ?? [] };
    })
    .filter((c): c is Cookbook => c !== null)
    .sort((a, b) => a.name.localeCompare(b.name));
}
