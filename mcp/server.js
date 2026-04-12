#!/usr/bin/env node
/**
 * MCP server: expose Clawvis skills as tools (stdio). Used by Claude Code via ~/.claude/claude.json
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { readdir, stat } from "fs/promises";
import { basename, isAbsolute, join, parse } from "path";
import { fileURLToPath } from "url";
import { homedir } from "os";
import { z } from "zod";

const __dirname = parse(fileURLToPath(import.meta.url)).dir;

async function readSkillDirs() {
  const raw = process.env.CLAWVIS_ROOT;
  let clawvisRoot;
  if (raw) {
    clawvisRoot = isAbsolute(raw) ? raw : join(homedir(), raw);
  } else {
    clawvisRoot = join(__dirname, "..");
  }

  const dirs = [];
  const coreSkills = join(clawvisRoot, "skills");
  const instName = process.env.INSTANCE_NAME || "example";
  const instSkills = join(clawvisRoot, "instances", instName, "skills");

  try {
    await stat(coreSkills);
    dirs.push(coreSkills);
  } catch {}
  try {
    await stat(instSkills);
    dirs.push(instSkills);
  } catch {}

  return dirs;
}

async function discoverSkills() {
  const skillDirs = await readSkillDirs();
  const skills = new Map();

  for (const skillDir of skillDirs) {
    try {
      const entries = await readdir(skillDir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith(".")) {
          if (!skills.has(entry.name)) {
            skills.set(entry.name, {
              path: join(skillDir, entry.name),
              description: `Clawvis skill: ${entry.name}`,
            });
          }
        }
      }
    } catch {
      /* skip */
    }
  }

  return Array.from(skills.values()).map((s) => ({
    name: basename(s.path),
    description: s.description,
  }));
}

async function main() {
  const skills = await discoverSkills();
  const server = new McpServer({ name: "clawvis-skills", version: "1.0.0" });

  for (const s of skills) {
    server.registerTool(
      s.name,
      {
        description: s.description,
        inputSchema: z.object({}),
      },
      async () => ({
        content: [
          {
            type: "text",
            text: `Skill "${s.name}" invocation not yet implemented. Skills are registered for discovery only.`,
          },
        ],
      }),
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
