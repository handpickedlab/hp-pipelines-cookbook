#!/usr/bin/env node
// Valideert alle cookbooks/*/cookbook.yaml tegen het manifest-schema.
// Gebruik: node index/scripts/validate.mjs (vereist `npm install` in index/).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parse } from "yaml";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const COOKBOOKS_DIR = path.join(ROOT, "cookbooks");

const TYPES = ["app", "workflow", "notebook"];
const RUNTIMES = ["node", "python-serverless", "python-server", "notebook", "none"];
const SLUG_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const KNOWN_KEYS = ["slug", "name", "description", "type", "runtime", "stack", "owner", "deploy", "url", "tags"];

const errors = [];

function check(slug, condition, message) {
  if (!condition) errors.push(`cookbooks/${slug}: ${message}`);
}

const dirs = fs.existsSync(COOKBOOKS_DIR)
  ? fs.readdirSync(COOKBOOKS_DIR, { withFileTypes: true }).filter((e) => e.isDirectory())
  : [];

if (dirs.length === 0) {
  console.log("Geen cookbooks gevonden — niets te valideren.");
  process.exit(0);
}

for (const dir of dirs) {
  const slug = dir.name;
  const manifestPath = path.join(COOKBOOKS_DIR, slug, "cookbook.yaml");

  if (!fs.existsSync(manifestPath)) {
    errors.push(`cookbooks/${slug}: cookbook.yaml ontbreekt`);
    continue;
  }

  let m;
  try {
    m = parse(fs.readFileSync(manifestPath, "utf8"));
  } catch (err) {
    errors.push(`cookbooks/${slug}: cookbook.yaml is geen geldige YAML (${err.message})`);
    continue;
  }

  check(slug, m && typeof m === "object", "manifest is leeg of geen object");
  if (!m || typeof m !== "object") continue;

  for (const key of Object.keys(m)) {
    check(slug, KNOWN_KEYS.includes(key), `onbekend veld "${key}" — schema wijzigen kan, maar dan ook validator/template/index updaten`);
  }

  check(slug, m.slug === slug, `slug "${m.slug}" moet gelijk zijn aan de mapnaam "${slug}"`);
  check(slug, SLUG_RE.test(slug), "mapnaam moet kebab-case zijn (a-z, 0-9, koppeltekens)");
  check(slug, typeof m.name === "string" && m.name.trim(), "name ontbreekt");
  check(slug, typeof m.description === "string" && m.description.trim(), "description ontbreekt");
  check(slug, TYPES.includes(m.type), `type "${m.type}" is ongeldig (${TYPES.join(" | ")})`);
  check(slug, RUNTIMES.includes(m.runtime), `runtime "${m.runtime}" is ongeldig (${RUNTIMES.join(" | ")})`);
  check(slug, Array.isArray(m.stack), "stack moet een lijst zijn");
  check(slug, typeof m.owner === "string" && m.owner.trim(), "owner ontbreekt");
  check(slug, typeof m.deploy === "boolean", "deploy moet true of false zijn");
  check(slug, m.tags === undefined || Array.isArray(m.tags), "tags moet een lijst zijn");
  check(slug, m.url === undefined || /^https?:\/\//.test(m.url), "url moet met http(s):// beginnen");

  if (m.runtime === "python-server") {
    check(slug, typeof m.url === "string" && m.url, "runtime python-server vereist een url (extern gehost)");
  }
  if (m.runtime === "none") {
    check(slug, m.deploy !== true, "runtime none kan geen deploy: true hebben");
  }

  check(slug, fs.existsSync(path.join(COOKBOOKS_DIR, slug, "HOSTING.md")), "HOSTING.md ontbreekt");
}

if (errors.length > 0) {
  console.error(`✖ ${errors.length} probleem${errors.length === 1 ? "" : "en"}:\n`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}

console.log(`✔ ${dirs.length} cookbook${dirs.length === 1 ? "" : "s"} gevalideerd, geen problemen.`);
