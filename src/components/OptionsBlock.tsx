import type { FC, ReactNode } from 'react';

interface OptionsBlockProps {
  children: ReactNode;
}

export const OptionsBlock: FC<OptionsBlockProps> = ({ children }) => {
  return (
    <div
      style={{
        padding: '10px',
        marginTop: '8px',
      }}
    >
      {children}
    </div>
  );
};
