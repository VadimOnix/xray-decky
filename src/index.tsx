import { definePlugin, ServerAPI } from 'decky-frontend-lib'
import { FC } from 'react'
import { FaNetworkWired } from 'react-icons/fa'
import { ConfigImport } from './components/ConfigImport'
import { ConnectionToggle } from './components/ConnectionToggle'
import { StatusDisplay } from './components/StatusDisplay'
import { TUNModeToggle } from './components/TUNModeToggle'
import { KillSwitchToggle } from './components/KillSwitchToggle'

// Main content component
const Content: FC<{ serverAPI: ServerAPI }> = ({ serverAPI }) => {
  return (
    <div>
      <ConfigImport serverAPI={serverAPI} />
      <StatusDisplay serverAPI={serverAPI} />
      <ConnectionToggle serverAPI={serverAPI} />
      <TUNModeToggle serverAPI={serverAPI} />
      <KillSwitchToggle serverAPI={serverAPI} />
    </div>
  )
}

export default definePlugin((serverAPI: ServerAPI) => {
  return {
    title: <div>Xray Decky</div>,
    content: <Content serverAPI={serverAPI} />,
    icon: <FaNetworkWired />,
  }
})
