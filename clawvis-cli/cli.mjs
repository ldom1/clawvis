#!/usr/bin/env node
import { Command } from "commander";
import boxen from "boxen";
import gradient from "gradient-string";
import figlet from "figlet";
import chalk from "chalk";
import { execSync, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";
import { createInterface } from "node:readline/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");
const LEGACY_BIN = path.join(ROOT_DIR, "clawvis");
const INSTALL_BIN = path.join(ROOT_DIR, "install.sh");

function detectVersion() {
  try {
    return execSync("git describe --tags --always", {
      cwd: ROOT_DIR,
      stdio: ["ignore", "pipe", "ignore"],
      encoding: "utf8",
    }).trim();
  } catch {
    return "dev";
  }
}

/** Couronne (mérovingien / Clawvis) au-dessus du figlet */
function clawvisLogoMark() {
  return chalk.hex("#fbbf24")("                         ♔");
}

function printHeader() {
  const funLines = [
    "Le roi des agents IA",
    "Ici pour servir la France !",
    "Roi des francs et des streamlined workflows",
    "Fais gaffe au vase de soissons",
    "Un Mérovingien en vaut plus que deux tu l'auras !",
    "Les Wisigoths et les IA blackbox n'ont qu'à bien se tenir !"
  ];
  const funLine = funLines[Math.floor(Math.random() * funLines.length)];
  const banner = figlet.textSync("Clawvis", { horizontalLayout: "default" });
  const prettyBanner = gradient.pastel.multiline(banner);
  const content = [
    clawvisLogoMark(),
    "",
    prettyBanner,
    "",
    `${chalk.bold("Version")} ${chalk.green(detectVersion())}`,
    `${chalk.cyan(funLine)}`,
  ].join("\n");
  console.log(
    boxen(content, {
      padding: 1,
      borderStyle: "round",
      borderColor: "magenta",
    }),
  );
}

function runLegacy(args = [], extraEnv = {}) {
  const child = spawn(LEGACY_BIN, args, {
    cwd: ROOT_DIR,
    stdio: "inherit",
    env: {
      ...mergedEnv(),
      CLAWVIS_NO_NODE_WRAPPER: "1",
      ...extraEnv,
    },
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

function frameAndRunLegacy(title, blurb, args, extraEnv = {}) {
  printHeader();
  console.log(
    boxen(
      [chalk.bold(title), "", chalk.dim(blurb)].join("\n"),
      {
        padding: { left: 1, right: 1, top: 0, bottom: 0 },
        borderStyle: "round",
        borderColor: "cyan",
      },
    ),
  );
  runLegacy(args, extraEnv);
}

const START_SCRIPT = path.join(ROOT_DIR, "scripts", "start.sh");
const SHUTDOWN_SCRIPT = path.join(ROOT_DIR, "scripts", "shutdown.sh");

function runShutdown() {
  const env = mergedEnv();
  const hubPort = env.HUB_PORT || "8088";
  const apiPort = env.KANBAN_API_PORT || "8090";
  const vitePort = env.HUB_VITE_PORT || "5173";
  printHeader();
  console.log(
    boxen(
      [
        chalk.bold("Arrêt du stack"),
        "",
        `${chalk.dim("Compose down")} + ports ${chalk.cyan(hubPort)}, ${chalk.cyan(apiPort)}, ${chalk.cyan(vitePort)}.`,
        "",
        `${chalk.dim("Ensuite :")} ${chalk.cyan("clawvis start")} ${chalk.dim("ou")} ${chalk.cyan("clawvis restart")}`,
      ].join("\n"),
      {
        padding: { left: 1, right: 1, top: 0, bottom: 0 },
        borderStyle: "round",
        borderColor: "cyan",
      },
    ),
  );
  const child = spawn("bash", [SHUTDOWN_SCRIPT], {
    cwd: ROOT_DIR,
    stdio: "inherit",
    env: { ...mergedEnv() },
  });
  child.on("exit", (code) => process.exit(code ?? 0));
}

/** Pretty entrypoint; runs start.sh directly (no bash clawvis `==>` line). */
function runStart() {
  const env = mergedEnv();
  const hubPort = env.HUB_PORT || "8088";
  const apiPort = env.KANBAN_API_PORT || "8090";
  const memoryPort = env.MEMORY_PORT || "3099";
  printHeader();
  console.log(
    boxen(
      [
        chalk.bold("Démarrage du stack de développement"),
        "",
        `${chalk.dim("Hub (Vite)")}     ${chalk.cyan(`http://localhost:${hubPort}/`)}`,
        `${chalk.dim("Kanban API")}    ${chalk.cyan(`http://localhost:${apiPort}/`)}`,
        `${chalk.dim("Brain (Logseq)")} ${chalk.cyan(`http://localhost:${memoryPort}/`)}`,
        "",
        chalk.yellow("Hub Docker sur 8088 ?") +
          " " +
          chalk.dim("`docker compose down` puis `clawvis shutdown`, ou change `HUB_PORT`."),
      ].join("\n"),
      {
        padding: { left: 1, right: 1, top: 0, bottom: 0 },
        borderStyle: "round",
        borderColor: "cyan",
      },
    ),
  );
  const child = spawn("bash", [START_SCRIPT], {
    cwd: ROOT_DIR,
    stdio: "inherit",
    env: {
      ...mergedEnv(),
      CLAWVIS_SKIP_START_ECHO: "1",
    },
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

function runRestart() {
  const env = mergedEnv();
  const hubPort = env.HUB_PORT || "8088";
  printHeader();
  console.log(
    boxen(
      [
        chalk.bold("Redémarrage"),
        "",
        chalk.dim("Arrêt propre (shutdown) puis relance du stack dev ou Docker."),
        `${chalk.dim("Hub")}  ${chalk.cyan(`http://localhost:${hubPort}/`)}`,
      ].join("\n"),
      {
        padding: { left: 1, right: 1, top: 0, bottom: 0 },
        borderStyle: "round",
        borderColor: "cyan",
      },
    ),
  );
  runLegacy(["restart"]);
}

/** Load `.env` so doctor works when not exported in the shell (process.env wins). */
function loadEnvFile() {
  const file = path.join(ROOT_DIR, ".env");
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, "utf8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const i = t.indexOf("=");
    if (i <= 0) continue;
    const k = t.slice(0, i).trim();
    let v = t.slice(i + 1).trim();
    if (
      (v.startsWith('"') && v.endsWith('"')) ||
      (v.startsWith("'") && v.endsWith("'"))
    ) {
      v = v.slice(1, -1);
    }
    out[k] = v;
  }
  return out;
}

function mergedEnv() {
  return { ...loadEnvFile(), ...process.env };
}

async function httpReachable(url, ms = 2500) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  try {
    const r = await fetch(url, { signal: ctrl.signal, redirect: "follow" });
    return r.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/** Bash forwards any args after `install` or `setup` to install.sh; bare command = interactive UI. */
function runInstallOrLegacyPassthrough(cmdName) {
  const idx = process.argv.indexOf(cmdName);
  const rest = idx >= 0 ? process.argv.slice(idx + 1) : [];
  if (rest.length === 0) {
    runInstallInteractive();
    return;
  }
  runLegacy([cmdName, ...rest]);
}

async function runDoctor() {
  const env = mergedEnv();
  const instanceName = env.INSTANCE_NAME || "example";
  const hubPort = env.HUB_PORT || "8088";
  const memoryPort = env.MEMORY_PORT || "3099";
  const memRel =
    env.MEMORY_ROOT || path.join("instances", instanceName, "memory");
  const instanceDir = path.join(ROOT_DIR, "instances", instanceName);
  const memoryRoot = path.isAbsolute(memRel)
    ? memRel
    : path.join(ROOT_DIR, memRel);

  const rows = [];
  let allOk = true;
  const row = (label, pass, hint = "") => {
    if (!pass) allOk = false;
    const mark = pass ? chalk.green("✓") : chalk.red("✗");
    const extra = hint ? chalk.dim(`  ${hint}`) : "";
    rows.push(`  ${mark}  ${label}${extra}`);
  };

  row("Dossier instance", fs.existsSync(instanceDir), path.relative(ROOT_DIR, instanceDir));
  row("Racine mémoire", fs.existsSync(memoryRoot), path.relative(ROOT_DIR, memoryRoot));

  const hubBase = `http://localhost:${hubPort}`;
  const checks = [
    ["Hub", `${hubBase}/`],
    ["Logs", `${hubBase}/logs/`],
    ["Kanban", `${hubBase}/kanban/`],
    ["Brain (page Hub)", `${hubBase}/memory/`],
    ["Brain (Logseq web)", `http://localhost:${memoryPort}/`],
  ];
  for (const [label, url] of checks) {
    const ok = await httpReachable(url);
    row(label, ok, url);
  }

  const footer = allOk
    ? chalk.green("Tout répond — stack probablement démarrée.")
    : chalk.yellow(
        "Certaines URLs ne répondent pas : lance `clawvis start` ou vérifie les ports dans `.env`.",
      );

  console.log(
    boxen(
      [
        chalk.bold("Clawvis doctor"),
        chalk.dim("Santé locale (fichiers + HTTP)"),
        "",
        ...rows,
        "",
        footer,
      ].join("\n"),
      {
        padding: { top: 0, bottom: 0, left: 1, right: 1 },
        margin: { top: 0, bottom: 1, left: 0, right: 0 },
        borderStyle: "round",
        borderColor: allOk ? "green" : "yellow",
      },
    ),
  );
  process.exit(allOk ? 0 : 1);
}

async function runInstallInteractive() {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    const I18N = {
      fr: {
        installHeading: "Installer Clawvis — le roi des francs et des agents IA",
        providerNote: chalk.dim("→ Connecter votre runtime IA se fait depuis le Hub (/setup/runtime/) ou via le CLI clawvis après le démarrage."),
        languageTitle: "Language / Langue:",
        languageFr: "1) Français (par défaut)",
        languageEn: "2) English",
        languageChoice: "Choix / Choice",
        instanceName: "Nom de l'instance",
        modeTitle: "Mode:",
        mode1Name: "Franc (Recommandé)",
        mode1Desc: "Démarrage rapide. Tout est configuré pour toi. (Nécessite docker)",
        mode2Name: "Mérovingien (Avancé)",
        mode2Desc: "Pour un déploiement serveur ou VPS. Ports et chemins configurables.",
        mode3Name: "Soissons (contribution)",
        mode3Desc: "Pour contribuer au projet open source Clawvis !",
        choice: "Choix",
        projectsRoot: "Dossier projets",
        hubPort: "Port Hub",
        brainPort: "Port Brain",
        kanbanApiPort: "Port Kanban API (mode dev)",
        continue: "Continuer ?",
        cancelled: "Installation annulée.",
        summaryInstance: "instance",
        summaryMode: "mode",
        summaryHubPort: "hub_port",
        summaryMemoryPort: "memory_port",
        summaryKanbanApiPort: "kanban_api_port",
        doneTitle: "Hub démarré !",
        doneTitleNoStart: "Instance prête (services non démarrés)",
        doneNoStartHint: "→ Lancez manuellement : docker compose up -d hub kanban-api hub-memory-api",
        doneHub: "Hub",
        doneBrain: "Brain",
        doneLogs: "Logs",
        doneKanban: "Kanban",
        doneSettings: "→ Configurer votre runtime IA",
      },
      en: {
        installHeading: "Install Clawvis — the king of the Franks and AI agents",
        providerNote: chalk.dim("→ Connect your AI runtime from the Hub (/setup/runtime/) or via the clawvis CLI after launch."),
        languageTitle: "Language / Langue:",
        languageFr: "1) Français (default)",
        languageEn: "2) English",
        languageChoice: "Choix / Choice",
        instanceName: "Instance name",
        modeTitle: "Mode:",
        mode1Name: "Franc (Recommended)",
        mode1Desc: "Fast launch. Everything is configured for you. (Requires Docker)",
        mode2Name: "Merovingian (Advanced)",
        mode2Desc: "For server or VPS deployments. Configure ports and paths manually.",
        mode3Name: "Soissons (contribution)",
        mode3Desc: "Contribute to the Clawvis open-source project!",
        choice: "Choice",
        projectsRoot: "Projects root path",
        hubPort: "Hub port",
        brainPort: "Brain port",
        kanbanApiPort: "Kanban API port (dev mode)",
        continue: "Continue?",
        cancelled: "Install cancelled.",
        summaryInstance: "instance",
        summaryMode: "mode",
        summaryHubPort: "hub_port",
        summaryMemoryPort: "memory_port",
        summaryKanbanApiPort: "kanban_api_port",
        doneTitle: "Hub is running!",
        doneTitleNoStart: "Instance ready (services not started)",
        doneNoStartHint: "→ Start manually: docker compose up -d hub kanban-api hub-memory-api",
        doneHub: "Hub",
        doneBrain: "Brain",
        doneLogs: "Logs",
        doneKanban: "Kanban",
        doneSettings: "→ Connect your AI runtime",
      },
    };

    let lang = "fr";
    let t = (k) => I18N.fr[k];

    const ask = async (q, d) => {
      const s = await rl.question(d !== undefined ? `${q} [${d}]: ` : `${q}: `);
      return s.trim() || d;
    };
    const yn = async (q, d = false) => {
      const def = d ? "Y/n" : "y/N";
      const s = await rl.question(`${q} (${def}): `);
      if (!s.trim()) return d;
      return /^(y|yes|o|oui)$/i.test(s.trim());
    };

    printHeader();
    console.log("");
    console.log(t("languageTitle"));
    console.log(t("languageFr"));
    console.log(t("languageEn"));
    const langPick = Number(await ask(t("languageChoice"), 1));
    lang = langPick === 2 ? "en" : "fr";
    t = (k) => I18N[lang][k];

    console.log("");
    console.log(chalk.bold(t("installHeading")));
    console.log(t("providerNote"));

    const user = process.env.USER || "user";
    const instance = await ask(t("instanceName"), user);

    console.log("");
    console.log(t("modeTitle"));
    console.log(`1) ${chalk.bold(t("mode1Name"))}`);
    console.log(`   ${chalk.dim(t("mode1Desc"))}`);
    console.log(`2) ${chalk.bold(t("mode2Name"))}`);
    console.log(`   ${chalk.dim(t("mode2Desc"))}`);
    console.log(`3) ${chalk.bold(t("mode3Name"))}`);
    console.log(`   ${chalk.dim(t("mode3Desc"))}`);

    const modePick = Number(await ask(t("choice"), 1));
    const mode = modePick <= 2 ? "docker" : "dev";
    const modeDisplay = modePick === 1 ? t("mode1Name") : modePick === 2 ? t("mode2Name") : t("mode3Name");

    const projectsRoot = await ask(t("projectsRoot"), `/home/${user}/lab_perso/projects`);
    let hubPort = "8088";
    let memoryPort = "3099";
    let kanbanApiPort = "8090";
    if (modePick >= 2) {
      hubPort = await ask(t("hubPort"), hubPort);
      memoryPort = await ask(t("brainPort"), memoryPort);
      kanbanApiPort = await ask(t("kanbanApiPort"), kanbanApiPort);
    }

    console.log("");
    console.log(
      boxen(
        [
          `${chalk.dim(t("summaryInstance"))}: ${chalk.green(instance)}`,
          `${chalk.dim(t("summaryMode"))}: ${chalk.green(modeDisplay)}`,
          `${chalk.dim(t("summaryHubPort"))}: ${chalk.green(hubPort)}`,
          `${chalk.dim(t("summaryMemoryPort"))}: ${chalk.green(memoryPort)}`,
        ].join("\n"),
        { padding: 1, borderStyle: "round", borderColor: "magenta" },
      ),
    );

    const ok = await yn(t("continue"), true);
    if (!ok) return;

    const args = [
      "--non-interactive",
      "--skip-primary",
      "--instance", instance,
      "--hub-port", hubPort,
      "--memory-port", memoryPort,
      "--kanban-api-port", kanbanApiPort,
      "--projects-root", projectsRoot,
      "--mode", mode,
      ...(modePick === 2 ? ["--no-start"] : []),
    ];

    const child = spawn("bash", [INSTALL_BIN, ...args], {
      cwd: ROOT_DIR,
      stdio: "inherit",
      env: { ...process.env, CLAWVIS_NO_NODE_WRAPPER: "1" },
    });
    child.on("exit", (code) => {
      if (code === 0) {
        console.log("");
        const noStart = modePick === 2;
        console.log(
          boxen(
            noStart
              ? [
                  chalk.bold(t("doneTitleNoStart")),
                  "",
                  chalk.yellow(t("doneNoStartHint")),
                ].join("\n")
              : [
                  chalk.bold(t("doneTitle")),
                  "",
                  `${t("doneHub")}:     ${chalk.cyan(`http://localhost:${hubPort}`)}`,
                  `${t("doneBrain")}:   ${chalk.cyan(`http://localhost:${hubPort}/memory/`)}`,
                  `${t("doneLogs")}:    ${chalk.cyan(`http://localhost:${hubPort}/logs/`)}`,
                  `${t("doneKanban")}: ${chalk.cyan(`http://localhost:${hubPort}/kanban/`)}`,
                  "",
                  chalk.yellow(`${t("doneSettings")}: http://localhost:${hubPort}/setup/runtime/`),
                ].join("\n"),
            { padding: 1, borderStyle: "round", borderColor: noStart ? "yellow" : "green" },
          ),
        );
      }
      process.exit(code ?? 1);
    });
  } catch (err) {
    if (err?.code === "ABORT_ERR" || err?.name === "AbortError") {
      console.log(`\n${chalk.yellow("Install cancelled.")}`);
      process.exit(130);
    }
    throw err;
  } finally {
    rl.close();
  }
}

// Parity avec le bash `clawvis` : mêmes sous-commandes ; la plupart délèguent via
// runLegacy (CLAWVIS_NO_NODE_WRAPPER=1). Exceptions : install/setup sans args (UI
// interactive), doctor (entièrement Node).
const program = new Command();
program
  .name("clawvis")
  .description("CLI pour Clawvis et pour les francs.")
  .version(detectVersion(), "-v, --version", "Show version")
  .showHelpAfterError("(tip) run clawvis --help");

program
  .command("help")
  .description("Aide avec bannière (équivalent bash `clawvis help`)")
  .action(() => {
    printHeader();
    console.log("");
    program.help({ error: false });
  });

program
  .command("install")
  .allowUnknownOption(true)
  .allowExcessArguments(true)
  .description(
    "Install: interactive wizard, or pass flags (e.g. --non-interactive) to install.sh",
  )
  .action(() => runInstallOrLegacyPassthrough("install"));
program
  .command("setup")
  .allowUnknownOption(true)
  .allowExcessArguments(true)
  .description("Same as install (bash parity)")
  .action(() => runInstallOrLegacyPassthrough("setup"));

program
  .command("start")
  .description("Start local dev stack (bannière + start.sh)")
  .action(() => runStart());
program
  .command("deploy")
  .description("Deploy stack over SSH")
  .action(() =>
    frameAndRunLegacy(
      "Déploiement",
      "SSH / stack selon votre instance.",
      ["deploy"],
    ),
  );
program
  .command("doctor")
  .description("Check hub, logs, kanban and brain health (pretty UI)")
  .action(async () => {
    await runDoctor();
  });

program
  .command("shutdown")
  .description("Stop compose + free Hub / Kanban / Memory API / Vite dev ports")
  .action(() => runShutdown());

program
  .command("restart")
  .description("Shutdown then start stack (no upgrade)")
  .action(() => runRestart());

const skillsCmd = program
  .command("skills")
  .description(
    "OpenClaw: point skills.load.extraDirs at repo skills/ + instance skills/; restart gateway",
  );
skillsCmd
  .command("sync")
  .description(
    "Patch openclaw.json extraDirs (jq), drop managed symlinks, openclaw gateway restart + skills list + doctor",
  )
  .action(() => runLegacy(["skills", "sync"]));

const update = program.command("update").description("Upgrade Clawvis release/channel");
update
  .option("--tag <ref>", "Update to a git ref")
  .option("--channel <channel>", "stable|beta|dev")
  .option("--dry-run", "Preview update without applying")
  .action((opts) => {
    const args = ["update"];
    if (opts.tag) args.push("--tag", opts.tag);
    if (opts.channel) args.push("--channel", opts.channel);
    if (opts.dryRun) args.push("--dry-run");
    frameAndRunLegacy(
      "Mise à jour Clawvis",
      "Applique le tag ou le canal demandé.",
      args,
    );
  });
update.command("status").option("--json", "JSON output").action((opts) => {
  const args = ["update", "status"];
  if (opts.json) args.push("--json");
  if (opts.json) {
    runLegacy(args);
    return;
  }
  frameAndRunLegacy(
    "Mise à jour — statut",
    "Révision git et chemins instance.",
    args,
  );
});
update
  .command("wizard")
  .description("Guided tag picker")
  .action(() =>
    frameAndRunLegacy(
      "Mise à jour — assistant",
      "Choix de tag guidé.",
      ["update", "wizard"],
    ),
  );

const backup = program.command("backup").description("Backup operations");
backup
  .command("create")
  .option("--json", "JSON output")
  .action((opts) => {
    const args = ["backup", "create"];
    if (opts.json) args.push("--json");
    if (opts.json) {
      runLegacy(args);
      return;
    }
    frameAndRunLegacy(
      "Sauvegarde",
      "Création d’une archive de l’instance.",
      args,
    );
  });
backup.command("list").action(() =>
  frameAndRunLegacy(
    "Sauvegardes",
    "Liste des archives disponibles.",
    ["backup", "list"],
  ),
);

program
  .command("restore <backupId>")
  .description("Restore a backup")
  .action((backupId) =>
    frameAndRunLegacy(
      "Restauration",
      `Backup : ${backupId}`,
      ["restore", backupId],
    ),
  );

program
  .command("uninstall")
  .option("--all", "Full uninstall")
  .option("--yes", "Confirm")
  .option("--dry-run", "Preview uninstall steps")
  .action((opts) => {
    const args = ["uninstall"];
    if (opts.all) args.push("--all");
    if (opts.yes) args.push("--yes");
    if (opts.dryRun) args.push("--dry-run");
    frameAndRunLegacy(
      "Désinstallation",
      "Prévisualisation ou suppression selon les options.",
      args,
    );
  });

// clawvis setup provider — intercepted before commander routing
// (The top-level `setup` command is a passthrough alias for install.)
if (process.argv[2] === "setup" && process.argv[3] === "provider") {
  runSetupProvider(process.argv.slice(4));
  // runSetupProvider calls process.exit or falls through
}

// clawvis setup quartz — delegates to scripts/setup-quartz.sh
if (process.argv[2] === "setup" && process.argv[3] === "quartz") {
  runLegacy(["setup", "quartz", ...process.argv.slice(4)]);
}

function runSetupProvider(args) {
  const env = mergedEnv();
  const hubPort = env.HUB_PORT || "8088";
  const current = env.PRIMARY_AI_PROVIDER || "(not set)";
  const claudeSet = !!(env.CLAUDE_API_KEY || "").trim();
  const mistralSet = !!(env.MISTRAL_API_KEY || "").trim();
  const openclawSet =
    !!(env.OPENCLAW_BASE_URL || "").trim() &&
    env.OPENCLAW_BASE_URL !== "http://localhost:3333";

  // Flag parsing: --provider, --key, --url
  let provider = "";
  let key = "";
  let url = "";
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--provider" && args[i + 1]) provider = args[++i];
    else if (args[i] === "--key" && args[i + 1]) key = args[++i];
    else if (args[i] === "--url" && args[i + 1]) url = args[++i];
  }

  if (provider || key || url) {
    // Write to .env via bash setup-runtime passthrough
    const extraArgs = [];
    if (provider) extraArgs.push("--provider", provider);
    if (key) {
      if (provider === "claude" || (!provider && claudeSet))
        extraArgs.push("--claude-api-key", key);
      else if (provider === "mistral")
        extraArgs.push("--mistral-api-key", key);
      else if (provider === "openclaw")
        extraArgs.push("--openclaw-api-key", key);
    }
    if (url) extraArgs.push("--openclaw-base-url", url);
    runLegacy(["setup-runtime", "--non-interactive", ...extraArgs]);
    return;
  }

  printHeader();
  console.log(
    boxen(
      [
        chalk.bold("AI Runtime — configuration actuelle"),
        "",
        `${chalk.dim("Provider actif")} : ${chalk.cyan(current)}`,
        `${chalk.dim("Claude")}         : ${claudeSet ? chalk.green("configuré") : chalk.yellow("non configuré")}`,
        `${chalk.dim("Mistral")}        : ${mistralSet ? chalk.green("configuré") : chalk.yellow("non configuré")}`,
        `${chalk.dim("OpenClaw")}       : ${openclawSet ? chalk.green("configuré") : chalk.yellow("non configuré")}`,
        "",
        chalk.bold("Pour configurer :"),
        "",
        `${chalk.cyan("A)")} Hub Settings (recommandé) :`,
        `   ${chalk.green(`http://localhost:${hubPort}/setup/runtime/`)} → section "AI Runtime"`,
        "",
        `${chalk.cyan("B)")} Ligne de commande :`,
        `   ${chalk.dim("clawvis setup provider --provider claude --key sk-ant-...")}`,
        `   ${chalk.dim("clawvis setup provider --provider mistral --key ...")}`,
        `   ${chalk.dim("clawvis setup provider --provider openclaw --url http://host:3333")}`,
        "",
        `${chalk.cyan("C)")} Fichier .env :`,
        `   ${chalk.dim("CLAUDE_API_KEY / MISTRAL_API_KEY / OPENCLAW_BASE_URL")}`,
        `   ${chalk.dim("Then: docker compose restart  (or clawvis restart)")}`,
      ].join("\n"),
      {
        padding: 1,
        borderStyle: "round",
        borderColor: current === "(not set)" ? "yellow" : "green",
      },
    ),
  );
  process.exit(0);
}

if (process.argv.length <= 2 || process.argv.includes("--help") || process.argv.includes("-h")) {
  printHeader();
}

program.parse(process.argv);
