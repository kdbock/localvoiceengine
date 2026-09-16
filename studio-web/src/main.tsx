import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';
import { App } from './App';
import { LocalStudio } from './LocalStudio';

const Studio = import.meta.env.VITE_LOCAL_MODE === 'true' ? LocalStudio : App;
createRoot(document.getElementById('root')!).render(<StrictMode><Studio /></StrictMode>);
