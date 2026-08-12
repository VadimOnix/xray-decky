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
    changelog: string;
    help: string;
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
    tunTitle: string;
    tunHtml: string;
  };

  usageTitle: string;
  usage: UsageStep[];

  faqTitle: string;
  faq: FaqItem[];

  footer: {
    /** Labels only, in display order — hrefs are structural and live in Base.astro. */
    links: string[];
    copy: string;
  };

  // guide: a later task adds a `guide` group here for the step-by-step
  // usage guide pages (ru/zh/fa/es share Landing.astro but link out to a
  // localized guide) — left out for now, EN parity port has no guide pages.
}
