import type { Brand } from './types';
export const starterBrands: Brand[] = [
  ['magic-mile-media', 'Magic Mile Media', '#402657', '#e0ae55', 'https://www.magicmilemedia.com', 'https://www.magicmilemedia.com/blog?format=rss'],
  ['neuse-news', 'Neuse News', '#111111', '#bf9737', 'https://www.neusenews.com', 'https://www.neusenews.com/index?format=rss'],
  ['neuse-news-sports', 'Neuse News Sports', '#111111', '#bf9737', 'https://www.neusenewssports.com', 'https://www.neusenewssports.com/news-1?format=rss'],
  ['neuse-news-sports-wayne', 'Neuse News Sports Wayne', '#173d63', '#6ba4d8', 'https://www.nnswayne.com', 'https://www.nnswayne.com/news?format=rss'],
  ['nc-business-desk', 'NC Business Desk', '#275f50', '#b56d4c', 'https://ncbusinessdesk.com', 'https://ncbusinessdesk.com/feed/'],
  ['nc-political-news', 'NC Political News', '#00286c', '#c80025', 'https://www.ncpoliticalnews.com', 'https://www.ncpoliticalnews.com/news?format=rss'],
].map(([id, name, primary, accent, site, feed]) => ({ id, name, site, feeds: [{ id: 'primary', label: 'Primary newsroom feed', url: feed, enabled: true }], colors: { primary, accent, ink: '#17212a', paper: '#ffffff' }, voice: { provider: 'qwen', profileName: `${name} primary voice`, model: 'Qwen3-TTS', instructions: 'Clear, warm, trustworthy local-news narration. Never theatrical.' } }));
