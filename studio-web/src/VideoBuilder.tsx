import { useState, type CSSProperties } from 'react';
import { doc, serverTimestamp, updateDoc } from 'firebase/firestore';
import { db } from './firebase';
import type { Brand } from './types';
import type { FeedStory } from './feed-cache';
import './video-builder.css';
import './approved-ncpn.css';

export function VideoBuilder({ brand, story, packageId, onClose }: { brand: Brand; story: FeedStory; packageId: string; onClose: () => void }) {
  const [format, setFormat] = useState('News update');
  const [script, setScript] = useState(`${story.title}. ${story.description} Read the full story at ${brand.site?.replace(/^https?:\/\//, '') || brand.name}.`);
  const [saved, setSaved] = useState(false);
  const save = async (ready = false) => { await updateDoc(doc(db, 'packages', packageId), { format, script, status: ready ? 'review' : 'drafting', updatedAt: serverTimestamp() }); setSaved(true); };
  return <main className="builder" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}><header className="builder-top"><button onClick={onClose}>← Story desk</button><p>{brand.name} · video package</p><a href={story.link} target="_blank" rel="noreferrer">Read original ↗</a></header><section className="builder-main"><div className="builder-copy"><p className="eyebrow">Step 1 of 3 · Shape the story</p><h1>{story.title}</h1><p className="source-summary">{story.description}</p><div className="format-choice"><p className="eyebrow">Video format</p>{['News update', 'Three things to know', 'Explainer', 'Quote-led'].map(item => <button key={item} className={format === item ? 'active' : ''} onClick={() => setFormat(item)}>{item}</button>)}</div><label className="script-field"><span>Spoken script</span><textarea value={script} onChange={event => setScript(event.target.value)} /><small>Make this sound like your newsroom—not like an AI wrote it.</small></label><div className="builder-actions"><button className="save-draft" onClick={() => save(false)}>Save draft</button><button className="send-review" onClick={() => save(true)}>Ready for visual design →</button>{saved && <span>Saved</span>}</div></div><aside className="video-preview"><p className="eyebrow">Approved visual · Headline card</p><div className="phone approved"><div className="preview-top">{brand.logoUrl ? <img src={brand.logoUrl} alt={brand.name} /> : brand.name}</div><strong className="preview-headline">{story.title}</strong><div className="story-image-card"><div><b>{story.title.split(' ').slice(0, 3).join(' ')}.</b><span>Story image</span></div></div><div className="lower-caption">{story.description}</div></div><p>This is the approved N.C. Political News reel treatment. The story’s lead image will replace the image card when feed-image import is connected.</p></aside></section></main>;
}
