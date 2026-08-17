/**
 * Shape of a per-locale copy dictionary. Landing.astro and Base.astro read
 * every piece of human-readable text through this type — no locale ever
 * hardcodes prose in the component tree.
 *
 * Strings that carry inline markup (`<b>`, `<code>`, links, `<br>`) are
 * suffixed `Html` and rendered with `set:html`. Plain strings are rendered
 * as text and are safe to interpolate directly.
 *
 * Pure structural/branding tokens that don't need translation (the
 * "XRAY DECKY" logo text, protocol names, city names in the hero demo
 * mockup) are intentionally NOT part of this dictionary and stay as literal
 * markup in Landing.astro — see the component for the exact list.
 */

export interface HeroStat {
  /** Present for the two count-up stats (protocols, tests); animated by demo.js. */
  countup?: number;
  /** Present for the two static stats (languages, license). */
  value?: string;
  label: string;
}

export interface FeatureItem {
  title: string;
  html: string;
}

export interface InstallMethod {
  title: string;
  stepsHtml: string[];
}

export interface UsageStep {
  number: string;
  title: string;
  body: string;
}

export interface FaqItem {
  q: string;
  html: string;
}

export interface Dict {
  seo: {
    title: string;
    description: string;
  };

  nav: {
    ariaLabel: string;
    features: string;
    panel: string;
    install: string;
    guide: string;
    changelog: string;
    help: string;
    donate: string;
    github: string;
  };

  hero: {
    badgeStable: string;
    badgeContext: string;
    titleHtml: string;
    purpose: string;
    ctaInstall: string;
    ctaGithub: string;
    statsAriaLabel: string;
    stats: HeroStat[];
    demoAriaLabel: string;
    /**
     * Initial (pre-JS) text for the animated deck+phone demo. demo.js takes
     * over immediately on load and currently hardcodes its own English
     * state labels (Connecting…, Connected, …) — full localization of the
     * running animation is deferred to the task that ports
     * public/scripts/demo.js itself. These values only cover the idle
     * snapshot rendered before/without that script.
     */
    demo: {
      deckStatus: string;
      enableConnection: string;
      phonePill: string;
      phoneStatus: string;
      phoneSub: string;
    };
    demoCaption: string;
  };

  protocols: {
    ariaLabel: string;
    chips: string[];
    note: string;
  };

  featuresTitle: string;
  features: FeatureItem[];

  panel: {
    titleHtml: string;
    introHtml: string;
    list: string[];
    securityHtml: string;
  };

  install: {
    title: string;
    prereqTitle: string;
    prereqHtml: string[];
    methods: InstallMethod[];
    /** Why the Plugin Store is not one of the methods. Rendered under them. */
    noteHtml: string;
    tunTitle: string;
    tunHtml: string;
  };

  usageTitle: string;
  usage: UsageStep[];

  faqTitle: string;
  faq: FaqItem[];

  /**
   * Crypto donation section. Prose only — the wallet addresses themselves are
   * locale-independent and live in site/src/lib/donations.ts, so a translation
   * can never drift them.
   */
  donate: {
    title: string;
    intro: string;
    assetHeader: string;
    networkHeader: string;
    addressHeader: string;
    /** Copy-button label and its post-click confirmation (see scripts/donate.js). */
    copy: string;
    copied: string;
  };

  footer: {
    /** Labels only, in display order — hrefs are structural and live in Base.astro. */
    links: string[];
    copy: string;
  };

  /**
   * Step-by-step "How to Set Up a VPN on Steam Deck" guide
   * (site/src/pages/vpn-on-steam-deck.astro + Guide.astro). It has its own
   * SEO title/description (`guide.seo`, distinct from the landing's `seo`)
   * and its own body copy. EN-only for now — ru/zh/fa/es dicts add their
   * own `guide` group once the page is translated (Task 7).
   */
  guide: {
    seo: {
      title: string;
      description: string;
    };
    h1: string;
    intro: string;
    whyTun: {
      title: string;
      body: string;
    };
    prereqTitle: string;
    prereqHtml: string[];
    stepsTitle: string;
    /** Each entry is a bold lead + body, e.g. '<b>Install X</b> — do Y.' */
    stepsHtml: string[];
    troubleshootingTitle: string;
    troubleshootingHtml: string;
  };
}
