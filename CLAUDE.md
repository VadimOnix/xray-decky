# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The single source of truth for repo guidance is @AGENTS.md — it covers commands, architecture, conventions and the feature workflow. Keep it up to date instead of this file; add here only what is Claude Code-specific.

## Claude Code specifics

- Project skills in `.claude/skills/`: `decky-plugin-dev` (Decky plugin platform patterns), `decky-deploy-debug` (deploy/watch/debug on a real Deck), `decky-release` (release flow), `react-decky-ui` (React inside the Steam CEF), `python-decky-backend` (asyncio backend patterns), `site-astro` (marketing site URL/SEO contract + Pages deploy).
- Fresh git worktrees need `pnpm install` before building or testing.
