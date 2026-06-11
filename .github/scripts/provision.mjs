#!/usr/bin/env node
// Maakt Vercel-projecten aan voor cookbooks met `deploy: true` die er nog geen hebben.
// Draait in CI na elke merge naar main (zie .github/workflows/provision.yml).
//
// Per nieuw project: naam `cookbook-<slug>`, gekoppeld aan deze GitHub-repo,
// root directory `cookbooks/<slug>/src`, ignored-build-step zodat alleen
// wijzigingen aan het eigen cookbook een build triggeren, plus een eerste deploy.
//
// Vereist: VERCEL_TOKEN (env), `npm ci` in index/ (voor de yaml-parser).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
// De yaml-parser is geïnstalleerd in index/ — resolve vanaf daar.
const { parse } = createRequire(path.join(ROOT, "index", "package.json"))("yaml");
const COOKBOOKS_DIR = path.join(ROOT, "cookbooks");

const TOKEN = process.env.VERCEL_TOKEN;
const TEAM_ID = process.env.VERCEL_TEAM_ID || "team_1i7tb4g93uky42oDmqCyjAF6"; // handpicked-lab
const GITHUB_REPO = "handpickedlab/hp-pipelines-cookbook";
const PROVISIONABLE_RUNTIMES = ["node", "python-serverless"];

if (!TOKEN) {
  console.error("VERCEL_TOKEN ontbreekt.");
  process.exit(1);
}

async function api(method, endpoint, body) {
  const url = `https://api.vercel.com${endpoint}${endpoint.includes("?") ? "&" : "?"}teamId=${TEAM_ID}`;
  const res = await fetch(url, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

const manifests = fs
  .readdirSync(COOKBOOKS_DIR, { withFileTypes: true })
  .filter((e) => e.isDirectory())
  .map((e) => {
    const p = path.join(COOKBOOKS_DIR, e.name, "cookbook.yaml");
    return fs.existsSync(p) ? parse(fs.readFileSync(p, "utf8")) : null;
  })
  .filter(Boolean);

const wanted = manifests.filter((m) => m.deploy === true);
const skipped = wanted.filter((m) => !PROVISIONABLE_RUNTIMES.includes(m.runtime));
for (const m of skipped) {
  console.log(`⏭  ${m.slug}: deploy: true maar runtime "${m.runtime}" wordt extern gehost — overgeslagen.`);
}

const candidates = wanted.filter((m) => PROVISIONABLE_RUNTIMES.includes(m.runtime));
if (candidates.length === 0) {
  console.log("Geen cookbooks die een Vercel-project nodig hebben.");
  process.exit(0);
}

let failures = 0;

for (const m of candidates) {
  const projectName = `cookbook-${m.slug}`;
  const existing = await api("GET", `/v9/projects/${projectName}`);
  if (existing.status === 200) {
    console.log(`✓  ${m.slug}: project ${projectName} bestaat al.`);
    continue;
  }

  console.log(`＋ ${m.slug}: project ${projectName} aanmaken…`);
  const created = await api("POST", "/v11/projects", {
    name: projectName,
    rootDirectory: `cookbooks/${m.slug}/src`,
    gitRepository: { type: "github", repo: GITHUB_REPO },
    commandForIgnoringBuildStep: "git diff HEAD^ HEAD --quiet -- ../",
  });

  if (created.status !== 200) {
    console.error(`✖  ${m.slug}: aanmaken mislukt (${created.status}): ${JSON.stringify(created.data.error || created.data)}`);
    failures++;
    continue;
  }

  const repoId = created.data.link?.repoId;
  if (!repoId) {
    console.error(`✖  ${m.slug}: project aangemaakt maar geen git-koppeling — eerste deploy handmatig triggeren.`);
    failures++;
    continue;
  }

  const deploy = await api("POST", "/v13/deployments", {
    name: projectName,
    project: projectName,
    target: "production",
    gitSource: { type: "github", repoId, ref: "main" },
  });

  if (deploy.status >= 300) {
    console.error(`✖  ${m.slug}: project aangemaakt, maar eerste deploy mislukt (${deploy.status}): ${JSON.stringify(deploy.data.error || deploy.data)}`);
    failures++;
    continue;
  }

  console.log(`🚀 ${m.slug}: live op https://${projectName}.vercel.app (deploy ${deploy.data.id})`);
  console.log(`   → vergeet niet \`url: https://${projectName}.vercel.app\` in het manifest te zetten.`);
}

process.exit(failures > 0 ? 1 : 0);
