import { definePlugin } from '@decky/api'
import { FaNetworkWired } from 'react-icons/fa'
import { QRImportBlock } from './components/QRImportBlock'
import { ConfigImport } from './components/ConfigImport'
import { ConnectionToggle } from './components/ConnectionToggle'
import { StatusDisplay } from './components/StatusDisplay'
import { TUNModeToggle } from './components/TUNModeToggle'
import { KillSwitchToggle } from './components/KillSwitchToggle'

// Main content component (QR block first per FR-001)
function Content() {
  return (
    <div>
      <QRImportBlock />
      <ConfigImport />
      <StatusDisplay />
      <ConnectionToggle />
      <TUNModeToggle />
      <KillSwitchToggle />
    </div>
  )
}

// New Decky API: definePlugin takes no arguments
// https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration
export default definePlugin(() => {
  console.log('Xray Decky plugin initializing')

  return {
    name: 'Xray Decky',
    content: <Content />,
    icon: <FaNetworkWired />,
    onDismount() {
      console.log('Xray Decky plugin unloading')
    },
  }
})
