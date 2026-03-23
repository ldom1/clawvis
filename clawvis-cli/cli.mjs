#!/usr/bin/env node
import { Command } from "commander";
import boxen from "boxen";
import gradient from "gradient-string";
import figlet from "figlet";
import chalk from "chalk";
import { execSync, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
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

function runLegacy(args = []) {
  const child = spawn(LEGACY_BIN, args, {
    cwd: ROOT_DIR,
    stdio: "inherit",
    env: { ...process.env, CLAWVIS_NO_NODE_WRAPPER: "1" },
  });
  child.on("exit", (code) => process.exit(code ?? 1));
}

async function runInstallInteractive() {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    const I18N = {
      fr: {
        installHeading: "Installer Clawvis (création d'une instance locale)",
        languageTitle: "Language / Langue:",
        languageFr: "1) Français (par défaut)",
        languageEn: "2) English",
        languageChoice: "Choix / Choice",
        instanceName: "Nom de l'instance",
        modeTitle: "Mode:",
        mode1Name: "Production (Recommended)",
        mode1Desc:
          "Pour utiliser Clawvis au quotidien sur ton ordinateur, avec une experience complete prete a l'emploi.",
        mode2Name: "Production (Docker)",
        mode2Desc: "Pour un environnement stable et reproductible, base sur docker. Necessite d'avoir Docker installe.",
        mode3Name: "Dev (contribution)",
        mode3Desc: "Pour developper et contribuer au projet avec une boucle de travail rapide, base sur Docker.",
        mode4Name: "Dev light",
        mode4Desc: "Pour decouvrir et explorer l'outil sans configurer de runtime IA.",
        choice: "Choix",
        projectsRoot: "Dossier projets",
        hubPort: "Port Hub",
        brainPort: "Port Brain",
        kanbanApiPort: "Port Kanban API (mode dev)",
        providerPrompt: "Provider:",
        providerChoice: "Choix",
        providerOpenclaw: "1) OpenClaw (self-hosted)",
        providerClaude: "2) Claude Code (Anthropic API key)",
        providerMistral: "3) Mistral vibe (Mistral API key)",
        skipPrimaryPrompt: "Ignorer la configuration du runtime IA principal ?",
        providerSkipLabel: "skip",
        openclawBaseUrl: "URL de base OpenClaw",
        openclawApiKey: "Clé API OpenClaw (optionnel)",
        claudeApiKey: "Clé API Claude",
        mistralApiKey: "Clé API Mistral",
        continue: "Continuer ?",
        cancelled: "Installation annulée.",
        summaryInstance: "instance",
        summaryProvider: "provider",
        summaryMode: "mode",
        summaryHubPort: "hub_port",
        summaryMemoryPort: "memory_port",
        summaryKanbanApiPort: "kanban_api_port",
      },
      en: {
        installHeading: "Install Clawvis (create a local instance)",
        languageTitle: "Language / Langue:",
        languageFr: "1) Français (default)",
        languageEn: "2) English",
        languageChoice: "Choix / Choice",
        instanceName: "Instance name",
        modeTitle: "Mode:",
        mode1Name: "Production (Recommended)",
        mode1Desc: "Use Clawvis daily on your computer, with a complete ready-to-go experience.",
        mode2Name: "Production (Docker)",
        mode2Desc: "A stable and reproducible setup based on Docker. Docker is required.",
        mode3Name: "Dev (contribution)",
        mode3Desc: "Develop and contribute with a fast workflow, based on Docker.",
        mode4Name: "Dev light",
        mode4Desc: "Explore the tool without setting up the primary AI runtime.",
        choice: "Choice",
        projectsRoot: "Projects root path",
        hubPort: "Hub port",
        brainPort: "Brain port",
        kanbanApiPort: "Kanban API port (dev mode)",
        providerPrompt: "Provider:",
        providerChoice: "Choice",
        providerOpenclaw: "1) OpenClaw (self-hosted)",
        providerClaude: "2) Claude Code (Anthropic API key)",
        providerMistral: "3) Mistral vibe (Mistral API key)",
        skipPrimaryPrompt: "Ignore the primary AI runtime configuration?",
        providerSkipLabel: "skip",
        openclawBaseUrl: "OpenClaw base URL",
        openclawApiKey: "OpenClaw API key (optional)",
        claudeApiKey: "Claude API key",
        mistralApiKey: "Mistral API key",
        continue: "Continue?",
        cancelled: "Install cancelled.",
        summaryInstance: "instance",
        summaryProvider: "provider",
        summaryMode: "mode",
        summaryHubPort: "hub_port",
        summaryMemoryPort: "memory_port",
        summaryKanbanApiPort: "kanban_api_port",
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
    console.log(t("installHeading"));

    const user = process.env.USER || "user";
    const instance = await ask(t("instanceName"), user);

    console.log("");
    console.log(t("modeTitle"));
    console.log(`1) ${t("mode1Name")}`);
    console.log(`   ${t("mode1Desc")}`);
    console.log(`2) ${t("mode2Name")}`);
    console.log(`   ${t("mode2Desc")}`);
    console.log(`3) ${t("mode3Name")}`);
    console.log(`   ${t("mode3Desc")}`);
    console.log(`4) ${t("mode4Name")}`);
    console.log(`   ${t("mode4Desc")}`);

    const modePick = Number(await ask(t("choice"), 1));
    const mode = modePick <= 2 ? "docker" : "dev";
    const modeDisplay = modePick === 1 ? t("mode1Name") : modePick === 2 ? t("mode2Name") : modePick === 3 ? t("mode3Name") : t("mode4Name");

    const projectsRoot = await ask(t("projectsRoot"), `/home/${user}/lab_perso/projects`);
    let hubPort = "8088";
    let memoryPort = "3099";
    let kanbanApiPort = "8090";
    if (mode === "dev") {
      hubPort = await ask(t("hubPort"), hubPort);
      memoryPort = await ask(t("brainPort"), memoryPort);
      kanbanApiPort = await ask(t("kanbanApiPort"), kanbanApiPort);
    }

    let provider = "claude";
    let providerLabel = provider;
    let openclawBaseUrl = "http://localhost:3333";
    let openclawApiKey = "";
    let claudeApiKey = "";
    let mistralApiKey = "";

    const skipPrimary = modePick === 4 ? true : mode === "dev" ? await yn(t("skipPrimaryPrompt"), true) : false;
    if (!skipPrimary) {
      console.log("");
      console.log(t("providerPrompt"));
      console.log(t("providerOpenclaw"));
      console.log(t("providerClaude"));
      console.log(t("providerMistral"));
      const providerPick = Number(await ask(t("providerChoice"), 2));
      provider = providerPick === 1 ? "openclaw" : providerPick === 2 ? "claude" : "mistral";
      providerLabel = provider;

      if (provider === "openclaw") {
        openclawBaseUrl = await ask(t("openclawBaseUrl"), openclawBaseUrl);
        openclawApiKey = await ask(t("openclawApiKey"), openclawApiKey);
      } else if (provider === "claude") {
        claudeApiKey = await ask(t("claudeApiKey"), claudeApiKey);
      } else {
        mistralApiKey = await ask(t("mistralApiKey"), mistralApiKey);
      }
    } else {
      providerLabel = t("providerSkipLabel");
    }

    console.log("");
    console.log(
      boxen(
        [
          `${t("summaryInstance")}: ${instance}`,
          `${t("summaryProvider")}: ${providerLabel}`,
          `${t("summaryMode")}: ${modeDisplay}`,
          `${t("summaryHubPort")}: ${hubPort}`,
          `${t("summaryMemoryPort")}: ${memoryPort}`,
          `${t("summaryKanbanApiPort")}: ${kanbanApiPort}`,
        ].join("\n"),
        { padding: 1, borderStyle: "round", borderColor: "magenta" },
      ),
    );

    const ok = await yn(t("continue"), true);
    if (!ok) return;

    const args = [
      "--non-interactive",
      "--instance",
      instance,
      "--hub-port",
      hubPort,
      "--memory-port",
      memoryPort,
      "--kanban-api-port",
      kanbanApiPort,
      "--projects-root",
      projectsRoot,
      "--mode",
      mode,
    ];

    if (skipPrimary) {
      args.push("--skip-primary");
    } else if (provider === "openclaw") {
      args.push("--provider", provider, "--openclaw-base-url", openclawBaseUrl, "--openclaw-api-key", openclawApiKey);
    } else if (provider === "claude") {
      args.push("--provider", provider, "--claude-api-key", claudeApiKey);
    } else {
      args.push("--provider", provider, "--mistral-api-key", mistralApiKey);
    }

    const child = spawn("bash", [INSTALL_BIN, ...args], {
      cwd: ROOT_DIR,
      stdio: "inherit",
      env: { ...process.env },
    });
    child.on("exit", (code) => process.exit(code ?? 1));
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

const program = new Command();
program
  .name("clawvis")
  .description("CLI pour Clawvis et pour les francs.")
  .version(detectVersion(), "-v, --version", "Show version")
  .showHelpAfterError("(tip) run clawvis --help");

program
  .command("install")
  .allowUnknownOption(true)
  .description("Install (interactive, pretty UI)")
  .action(() => runInstallInteractive());
program
  .command("setup")
  .allowUnknownOption(true)
  .description("Alias of install")
  .action(() => runInstallInteractive());

program.command("start").description("Start local dev stack").action(() => runLegacy(["start"]));
program.command("deploy").description("Deploy stack over SSH").action(() => runLegacy(["deploy"]));
program
  .command("doctor")
  .description("Check hub, logs, kanban and brain health")
  .action(() => runLegacy(["doctor"]));

program
  .command("restart")
  .description("Restart stack (no upgrade)")
  .action(() => runLegacy(["restart"]));

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
    runLegacy(args);
  });
update.command("status").option("--json", "JSON output").action((opts) => {
  const args = ["update", "status"];
  if (opts.json) args.push("--json");
  runLegacy(args);
});
update.command("wizard").description("Guided tag picker").action(() => runLegacy(["update", "wizard"]));

const backup = program.command("backup").description("Backup operations");
backup.command("create").option("--json", "JSON output").action((opts) => {
  const args = ["backup", "create"];
  if (opts.json) args.push("--json");
  runLegacy(args);
});
backup.command("list").action(() => runLegacy(["backup", "list"]));

program.command("restore <backupId>").description("Restore a backup").action((backupId) => {
  runLegacy(["restore", backupId]);
});

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
    runLegacy(args);
  });

if (process.argv.length <= 2 || process.argv.includes("--help") || process.argv.includes("-h")) {
  printHeader();
}

program.parse(process.argv);
