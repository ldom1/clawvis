#!/usr/bin/env node

/**
 * Minimal MCP server for Clawvis skills.
 * Exposes Clawvis skills as MCP tools that Claude Code can discover.
 * Stdio transport — called by Claude Code via ~/.claude/claude.json
 */

import { StdioServer } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { readdir, stat } from "fs/promises";
import { join, parse } from "path";
import { fileURLToPath } from "url";
import { homedir } from "os";

const __dirname = parse(fileURLToPath(import.meta.url)).dir;

// ============================================
// SKILL DISCOVERY
// ============================================

async function readSkillDirs() {
  /**
   * Discover skill directories from .env CLAWVIS_ROOT or repo root.
   * Look in: {clawvis_root}/skills and {clawvis_root}/instances/{name}/skills
   */
  const clawvisRoot = process.env.CLAWVIS_ROOT
    ? parse(process.env.CLAWVIS_ROOT).root === "/" ||
      process.env.CLAWVIS_ROOT[1] === ":"
      ? process.env.CLAWVIS_ROOT
      : join(homedir(), process.env.CLAWVIS_ROOT)
    : join(__dirname, "..");

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
  /**
   * List all skills from discovered directories.
   * Each skill is a subdirectory.
   */
  const skillDirs = await readSkillDirs();
  const skills = new Map(); // name -> { path, description }

  for (const skillDir of skillDirs) {
    try {
      const entries = await readdir(skillDir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory() && !entry.name.startsWith(".")) {
          // Treat each skill directory as a skill
          if (!skills.has(entry.name)) {
            skills.set(entry.name, {
              path: join(skillDir, entry.name),
              description: `Clawvis skill: ${entry.name}`,
            });
          }
        }
      }
    } catch (err) {
      // Silently skip missing directories
    }
  }

  return Array.from(skills.values()).map((s) => ({
    name: s.path.split("/").pop() || "unknown",
    description: s.description,
  }));
}

// ============================================
// MCP SERVER
// ============================================

const server = new StdioServer({
  name: "clawvis-skills",
  version: "1.0.0",
});

// List available tools (skills)
server.setRequestHandler(ListToolsRequestSchema, async () => {
  const skills = await discoverSkills();
  return {
    tools: skills.map((s) => ({
      name: s.name,
      description: s.description,
      inputSchema: {
        type: "object",
        properties: {},
        required: [],
      },
    })),
  };
});

// Call tool (skill)
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // At this stage, we don't execute skills.
  // Future: integrate with OpenClaw or skill runner.
  return {
    content: [
      {
        type: "text",
        text: `Skill "${request.params.name}" invocation not yet implemented. Skills are registered for discovery only.`,
      },
    ],
  };
});

// Start server
server.start();
