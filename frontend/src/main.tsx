import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ChainlitContext } from '@chainlit/react-client';
import { RecoilRoot } from 'recoil';
import { apiClient } from './api/chainlitClient';
import './index.css';
import App from './ui/App.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RecoilRoot>
      <ChainlitContext.Provider value={apiClient}>
        <App />
      </ChainlitContext.Provider>
    </RecoilRoot>
  </StrictMode>,
);