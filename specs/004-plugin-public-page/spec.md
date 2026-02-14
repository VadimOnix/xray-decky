# Feature Specification: Public Plugin Page with Steam Deck/SteamOS Styling

**Feature Branch**: `004-plugin-public-page`  
**Created**: 2026-02-14  
**Status**: Draft  
**Input**: User description: "изучи лучшие практики github gist и сделай публичную страницу плагина, сгенерируй картинки и медиаконтент для современного дизайна в стилистике steamdeck, steamos"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Understand the Plugin (Priority: P1)

A Steam Deck user or a visitor looking for a VLESS/proxy solution discovers the plugin through a public page. They see a clear value proposition, feature list, and visual identity consistent with Steam Deck/SteamOS so they immediately recognize the context and trust the source.

**Why this priority**: The public page is the first touchpoint; without clear discovery and understanding, installs and adoption drop.

**Independent Test**: Can be fully tested by opening the public page and verifying that a new visitor can state what the plugin does and for which platform, without reading external docs.

**Acceptance Scenarios**:

1. **Given** a visitor with no prior knowledge, **When** they open the public page, **Then** they see the plugin name, one-sentence purpose, and that it is for Steam Deck / Decky Loader.
2. **Given** the public page is open, **When** the visitor scrolls or reads, **Then** they see a concise list of main features (e.g. import VLESS, toggle connection, TUN mode, kill switch) and how to install or where to get it.
3. **Given** the public page, **When** viewed on desktop or mobile, **Then** content remains readable and key actions (e.g. link to store or install instructions) are accessible.

---

### User Story 2 - Recognizable Steam Deck/SteamOS Visual Identity (Priority: P1)

Visitors see a modern, cohesive design that evokes Steam Deck and SteamOS (colors, typography, layout conventions) so the page feels native to the ecosystem and not generic.

**Why this priority**: Visual consistency builds trust and helps the plugin be perceived as a first-class Steam Deck experience.

**Independent Test**: Can be tested by showing the page to someone familiar with Steam Deck/SteamOS and confirming they identify the style; and by checking that key visual elements (hero area, feature blocks, media) follow the same tone.

**Acceptance Scenarios**:

1. **Given** the public page, **When** a user views it, **Then** the overall look (color palette, card/section style, typography) aligns with common Steam Deck/SteamOS marketing and store conventions (dark theme, accent colors, clear hierarchy).
2. **Given** the public page, **When** images or media are present, **Then** they depict or suggest Steam Deck/SteamOS context (e.g. device, UI, or abstract visuals consistent with the brand) and are of sufficient quality for web display.
3. **Given** the public page, **When** viewed on different screen sizes, **Then** layout and media scale appropriately without breaking the intended style.

---

### User Story 3 - Shareable and Embeddable Content (Priority: P2)

The page or its content can be shared via a stable URL and, where the hosting option supports it, embedded (e.g. in docs, forums, or Gist-style snippets) so others can reference or showcase the plugin without duplicating long descriptions.

**Why this priority**: Shareability increases reach; embeddability supports documentation and community posts.

**Independent Test**: Can be tested by obtaining the public URL, sharing it in a message or post, and (if applicable) embedding a representative block and confirming it loads and displays correctly.

**Acceptance Scenarios**:

1. **Given** the public page is published, **When** a user copies the page URL, **Then** the URL is stable and opens the same content for anyone with access.
2. **Given** the hosting or format supports embedding, **When** a user embeds the designated content (e.g. description, feature list, or code snippet), **Then** the embedded content renders correctly in the target context (e.g. blog, Gist, or forum).
3. **Given** the content is shared, **When** viewed by a third party, **Then** no sensitive data (tokens, keys, user paths) is visible and the content is safe for public distribution.

---

### User Story 4 - Generated Images and Media (Priority: P2)

The feature includes generated or curated images and media (e.g. hero image, feature icons or screenshots, optional short visual guide) so the page is visually rich and suitable for modern landing pages and store assets.

**Why this priority**: Media improves comprehension and professionalism; store and docs often require at least one image.

**Independent Test**: Can be tested by checking that the page includes at least one hero or header image and at least one set of feature-related visuals (icons or images), and that they match the Steam Deck/SteamOS style.

**Acceptance Scenarios**:

1. **Given** the public page, **When** a visitor loads it, **Then** at least one primary visual (hero/banner or equivalent) is present and reflects Steam Deck/SteamOS styling.
2. **Given** the feature set of the plugin, **When** the page describes features, **Then** each major feature is supported by an image, icon, or short media element where appropriate.
3. **Given** generated or selected media, **When** used on the page, **Then** assets are web-appropriate (resolution, format, file size) and do not infringe third-party rights (e.g. use permitted or original assets).

---

### Edge Cases

- What happens when the public page is opened in a very old or restricted browser? Content should remain readable (progressive enhancement; critical text and links work without advanced features).
- How does the system handle missing or failed media? Placeholders or alt text ensure the page still communicates the plugin name and main message.
- What if the page is embedded in a context that blocks scripts or external images? Core information (plugin name, description, install link) should be available in plain text or static markup so the page degrades gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single public page that presents the plugin’s name, purpose (one sentence), target platform (Steam Deck / Decky Loader), and primary features.
- **FR-002**: The system MUST present installation or acquisition steps (or a clear link to them) so a visitor can proceed to install or find the plugin.
- **FR-003**: The public page MUST use a visual design consistent with Steam Deck/SteamOS (dark theme, recognizable color and layout conventions, modern typography).
- **FR-004**: The system MUST include at least one hero or header image and feature-related visuals (icons or images) that match the Steam Deck/SteamOS style and are suitable for web display.
- **FR-005**: The public page MUST be reachable via a stable, shareable URL that shows the same content to all visitors with access.
- **FR-006**: Where the chosen hosting or format supports it, the system MUST allow key content (e.g. description, feature list, or code) to be embedded in third-party pages (e.g. Gist, blog, forum) and render correctly.
- **FR-007**: The system MUST ensure that no secrets, tokens, or user-specific paths appear on the public page or in embeddable content.
- **FR-008**: The public page MUST remain usable when media fails to load (e.g. fallback text or placeholders) and when viewed on common desktop and mobile viewports.
- **FR-009**: All images and media used on the page MUST be legally safe for public use (original, licensed, or otherwise permitted).

### Key Entities

- **Public page**: The single public-facing artifact (e.g. one page or one Gist) that describes the plugin, its features, and how to get it; it has a stable URL and optional embed snippet.
- **Plugin identity**: Name, short description, feature list, and install/get link; these are the core data shown on the public page.
- **Media asset**: Any image or short visual used on the page (hero, feature graphic, icon set); each has a role (e.g. hero, feature), style alignment (Steam Deck/SteamOS), and usage rights.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new visitor can state the plugin’s name, purpose, and platform within 30 seconds of opening the public page.
- **SC-002**: At least one hero or header image and one set of feature-related visuals are present and align with Steam Deck/SteamOS style as judged by a reviewer familiar with the platform. Repeatability: reviewer checks (1) dark theme dominant, (2) accent color used for links/emphasis, (3) clear heading/section hierarchy.
- **SC-003**: The public page URL can be shared and opened by a third party without errors; where embedding is supported, the embedded content loads and displays correctly in at least one common embedding context.
- **SC-004**: The page renders correctly and remains readable on viewport widths typical for desktop (e.g. 1280px) and mobile (e.g. 375px).
- **SC-005**: No secrets, API keys, or user-specific paths are present on the public page or in provided embed snippets.

## Assumptions

- The plugin is the existing Xray Decky (VLESS proxy for Steam Deck); the public page describes this plugin only.
- “Public page” means one primary landing-style page (whether implemented as a Gist, GitHub Pages, or other host); the spec does not mandate a specific technology.
- “Steam Deck/SteamOS style” is interpreted from public Steam and Steam Deck branding (dark themes, accent colors, clear hierarchy); no access to proprietary Steamworks asset kits is assumed.
- Generated or curated images will be created or selected to avoid trademark misuse (e.g. no unauthorized Valve/Steam logos); style inspiration only.
- Gist best practices applied: clear description, single-purpose content, stable URL, optional embed; no requirement to host the entire page as a Gist if another option better serves the goals.
