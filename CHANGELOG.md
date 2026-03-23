# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

- Hub migrated to Vite app (`hub/src`) with shared onboarding navigation and mascot branding.
- Added onboarding pages for Logs, Brain, Kanban in Hub, including logs empty-state visibility.
- Added interactive project-scoped Kanban board in Hub with inline status updates.
- Added project tags support and display in project cards.
- Project creation now enforces memory page creation and uses memory page as project source of truth.
- Brain runtime integrated through Docker (`memory` service) with instance-scoped memory root support.
- Added memory initialization script with canonical structure (`projects/resources/daily/archive/todo`) and template seeds.
- Installer (`install.sh`) now provides guided setup for OpenClaw, Claude, or Mistral, plus instance naming.
- Added versioned upgrade workflow via `upgrade.sh <tag>` with smoke checks.
- Start/deploy workflows now rebuild Hub with Yarn before run/deploy.
- Added frontend formatter/test tooling in `hub/` (`prettier`, `jest`, and initial test).

