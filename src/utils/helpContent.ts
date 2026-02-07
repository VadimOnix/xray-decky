import type { HelpTopic } from '../types/ui'

export interface HelpContent {
  title: string
  body: string
}

const helpContent: Record<HelpTopic, HelpContent> = {
  'setup.qr_import': {
    title: 'QR import',
    body: 'Scan the QR code with your phone to open the import page on the same LAN.',
  },
  'setup.lan_address': {
    title: 'LAN address',
    body: 'Open the import URL from a device on the same local network.',
  },
  'setup.vless_link': {
    title: 'VLESS link',
    body: 'Paste your vless:// link or subscription. Invalid links are rejected and do not overwrite a valid config.',
  },
  'configured.status': {
    title: 'Status meanings',
    body: 'Connected: proxy active. Connecting: starting up. Blocked: kill switch active. Disconnected: idle.',
  },
  'configured.reset': {
    title: 'Reset configuration',
    body: 'Clears the saved configuration and returns to setup. Disabled while the connection is active.',
  },
  'options.tun_mode': {
    title: 'TUN mode',
    body: 'Routes all system traffic through the proxy. Requires elevated privileges from INSTALLATION.md.',
  },
  'options.kill_switch': {
    title: 'Kill switch',
    body: 'Blocks all traffic if the proxy disconnects unexpectedly. Enable only if you want strict leak prevention.',
  },
}

export const getHelpContent = (topic: HelpTopic): HelpContent => helpContent[topic]
