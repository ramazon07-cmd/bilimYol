import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const requiredTokens = [
  "#65001F",
  "#450417",
  "#7A1233",
  "#F5E8DC",
  "#FFF9F4",
  "#29161C",
  "#FFFFFF",
  "#DEC8BE",
  "#287A55",
  "#C68A22",
  "#B4233A",
];

const legacyPrimaryColors = [
  "#071b3a",
  "#4568a8",
  "#d79c10",
  "#c8564e",
  "#121f57",
  "#0c1b52",
  "#17276a",
  "#183d69",
  "#234c7c",
  "#274e83",
  "#3f68b7",
];

function sourceFiles(directory) {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    return statSync(path).isDirectory() ? sourceFiles(path) : [path];
  });
}

const appFiles = sourceFiles("app").filter((path) => /\.(css|ts|tsx)$/.test(path));
const appSource = appFiles.map((path) => readFileSync(path, "utf8")).join("\n").toLowerCase();
const themeSource = readFileSync("app/lib/rbis-theme.ts", "utf8");
const cssSource = readFileSync("app/globals.css", "utf8");

const missingTokens = requiredTokens.filter((token) => !themeSource.includes(token));
const legacyMatches = legacyPrimaryColors.filter((token) => appSource.includes(token.toLowerCase()));
const missingStandards = [
  ".workspace-sidebar nav button.active",
  ".portal-primary",
  ".portal-card",
  ".portal-table th",
  ".admin-modal-head",
  "@media print",
].filter((selector) => !cssSource.includes(selector));

if (missingTokens.length || legacyMatches.length || missingStandards.length) {
  console.error("RBIS theme validation failed.");
  if (missingTokens.length) console.error("Missing tokens:", missingTokens.join(", "));
  if (legacyMatches.length) console.error("Legacy colors:", legacyMatches.join(", "));
  if (missingStandards.length) console.error("Missing UI standards:", missingStandards.join(", "));
  process.exit(1);
}

console.log("RBIS design tokens and shared UI standards are valid.");
