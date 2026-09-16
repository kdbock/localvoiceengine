import type { Brand } from './types';
export const starterBrands: Brand[] = [
  ['magic-mile-media', 'Magic Mile Media', '#402657', '#e0ae55'],
  ['neuse-news', 'Neuse News', '#111111', '#bf9737'],
  ['neuse-news-sports', 'Neuse News Sports', '#111111', '#bf9737'],
  ['neuse-news-sports-wayne', 'Neuse News Sports Wayne', '#173d63', '#6ba4d8'],
  ['nc-business-desk', 'NC Business Desk', '#275f50', '#b56d4c'],
  ['nc-political-news', 'NC Political News', '#00286c', '#c80025'],
].map(([id, name, primary, accent]) => ({ id, name, colors: { primary, accent, ink: '#17212a', paper: '#ffffff' }, voice: { provider: 'qwen', profileName: `${name} primary voice`, model: 'Qwen3-TTS', instructions: 'Clear, warm, trustworthy local-news narration. Never theatrical.' } }));
