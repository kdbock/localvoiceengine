import { useState, type CSSProperties } from 'react';
import { doc, serverTimestamp, updateDoc } from 'firebase/firestore';
import { db } from './firebase';
import type { Brand } from './types';
import type { FeedStory } from './feed-cache';
import './video-builder.css';
import './approved-ncpn.css';
import './story-image.css';
import './scene-layout.css';

export function VideoBuilder({ brand, story, packageId, onClose }: { brand: Brand; story: FeedStory; packageId: string; onClose: () => void }) {
  const [format, setFormat] = useState('News update');
  const [script, setScript] = useState(`${story.title}. ${story.description} Read the full story at ${brand.site?.replace(/^https?:\/\//, '') || brand.name}.`);
  const [visualText, setVisualText] = useState(story.description.split(/(?<=[.!?])\s/)[0] || story.description);
  const [saved, setSaved] = useState(false);
  const save = async (ready = false) => { await updateDoc(doc(db, 'packages', packageId), { format, script, visualText, status: ready ? 'review' : 'drafting', updatedAt: serverTimestamp() }); setSaved(true); };
  return <main className="builder" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}>
    <header className="builder-top"><button onClick={onClose}>← Story desk</button><p>{brand.name} · video package</p><a href={story.link} target="_blank" rel="noreferrer">Read original ↗</a></header>
    <section className="builder-main"><div className="builder-copy"><p className="eyebrow">Step 1 of 3 · Shape the story</p><h1>{story.title}</h1><p className="source-summary">{story.description}</p><div className="format-choice"><p className="eyebrow">Video format</p>{['News update', 'Three things to know', 'Explainer', 'Quote-led'].map(item => <button key={item} className={format === item ? 'active' : ''} onClick={() => setFormat(item)}>{item}</button>)}</div><label className="script-field"><span>Spoken script</span><textarea value={script} onChange={event => setScript(event.target.value)} /><small>Make this sound like your newsroom—not like an AI wrote it.</small></label><label className="visual-field"><span>Scene 1 · on-screen support text</span><textarea value={visualText} onChange={event => setVisualText(event.target.value)} /><small>One concise thought that supports the spoken script. It is not a transcript.</small></label><div className="builder-actions"><button className="save-draft" onClick={() => save(false)}>Save draft</button><button className="send-review" onClick={() => save(true)}>Ready for visual design →</button>{saved && <span>Saved</span>}</div></div>
      <aside className="video-preview"><p className="eyebrow">Approved visual · Scene 1</p><div className="phone approved scene"><div className="preview-top">{brand.logoUrl ? <img src={brand.logoUrl} alt={brand.name} /> : brand.name}</div><strong className={`preview-headline ${story.title.length > 72 ? 'long-headline' : ''}`}>{story.title}</strong><div className="story-image-card">{story.imageUrl ? <img src={story.imageUrl} alt="Story lead visual" /> : <div><b>Lead image</b><span>Refresh stories to load</span></div>}</div><div className="lower-caption">{visualText}</div></div><p>Portrait story image, headline limited to two lines (three only when needed), and on-screen text that supports the voiceover.</p></aside>
    </section>
  </main>;
}
