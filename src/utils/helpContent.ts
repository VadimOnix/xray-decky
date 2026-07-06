import type { HelpTopic } from '../types/ui';
import { t } from './i18n';

export interface HelpContent {
  title: string;
  body: string;
}

/** Localized help title/body for a topic (see help.* keys in i18n). */
export const getHelpContent = (topic: HelpTopic): HelpContent => ({
  title: t(`help.${topic}.title`),
  body: t(`help.${topic}.body`),
});
