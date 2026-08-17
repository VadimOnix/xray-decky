---
name: seo-surfaces
description: Use when editing any README* file, plugin.json or package.json descriptions/keywords, marketing copy, donation addresses, or release notes — anything that changes user-facing wording about what this plugin is. Also use when a change might touch how the project appears in GitHub search or Google.
---

# SEO surfaces

This repo ranks for "steam deck vpn" because a fixed set of surfaces carry
consistent, deliberate wording. Editing one surface without the others
silently undoes that work. Full rules: AGENTS.md → "SEO surfaces".

## The one rule people break

**A content edit to README.md is an edit to five files.** README.ru.md,
README.zh-CN.md, README.fa.md and README.es.md mirror it section-for-section.
Translate the same change into all four in the same commit — do not ask
whether to, do not leave it for "a follow-up", do not treat "the README"
(singular) in a task as permission to touch only English.

Dev-only edits (build commands, project-structure tree) still count: the
structure blocks are mirrored verbatim.

## Surfaces checklist

| Surface | Where | Rule |
|---|---|---|
| Positioning phrase | everywhere | "VPN & proxy client for Steam Deck" — keep "VPN" AND "proxy" (honest: TUN = VPN-style, never "classic VPN") |
| "Steam Deck" | everywhere | two words, never "SteamDeck" (search tokenization) |
| README×5 | repo root | section-parity; switcher row; hero banner; same links |
| Repo description/topics | live via `gh api` | changes need maintainer sign-off |
| plugin.json `publish.description` | plugin metadata (no store listing — see decky-release) | keep in sync with README positioning |
| Install instructions | README×5, `site/src/i18n/*.ts` | installer script + release zip ONLY — never the Decky Plugin Store |
| Site copy | `site/src/i18n/*.ts` | see the site-astro skill for URL/SEO contract |
| Donation addresses | `site/src/lib/donations.ts` ONLY | never retype an address in a README or dict — copy from donations.ts |
| Terminology | README translations | they ARE the approved glossary (kill switch glosses, подписка/订阅/اشتراک/suscripción) |

## Verify before claiming done

```bash
node scripts/seo-check.mjs --readme                  # README×5 parity, addresses, banner
cd site && pnpm run check && pnpm build && cd .. \
  && node scripts/seo-check.mjs --site               # only if site/ changed
```

CI runs both; a red seo-check means fix the content — never delete the check.

## Red flags — stop and re-read this skill

- "The task said *the* README, so just README.md"
- "I'll ask whether to update translations" (the answer is always yes)
- "I'll retype this wallet address" / "the address is probably the same"
- Rewording that drops "VPN" or "proxy", or fuses "SteamDeck"
