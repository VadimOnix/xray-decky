import { FC } from 'react'
import { Field } from '@decky/ui'
import type { ConnectionConfigSummary } from '../types/ui'

interface ConfigSummaryCardProps {
  summary: ConnectionConfigSummary
}

export const ConfigSummaryCard: FC<ConfigSummaryCardProps> = ({ summary }) => {
  if (!summary.exists) {
    return null
  }

  const statusText = summary.isValid ? 'Valid' : 'Invalid'
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const
  const cardStyle = {
    padding: '10px',
    backgroundColor: '#1e3a5f',
    borderRadius: '6px',
  }

  return (
    <div style={cardStyle}>
      {summary.displayName && (
        <Field
          label="Name"
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.displayName}</span>}
        />
      )}
      {summary.endpoint && (
        <Field
          label="Endpoint"
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.endpoint}</span>}
        />
      )}
      <Field
        label="Status"
        bottomSeparator="none"
        description={<span style={leftDescriptionStyle}>{statusText}</span>}
      />
      {summary.validationError && (
        <Field
          label="Validation error"
          bottomSeparator="none"
          description={<span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>{summary.validationError}</span>}
        />
      )}
      {summary.source && (
        <Field
          label="Source"
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.source}</span>}
        />
      )}
    </div>
  )
}
