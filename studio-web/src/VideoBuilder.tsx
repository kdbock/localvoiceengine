import { useState, type CSSProperties } from 'react';
import { doc, serverTimestamp, updateDoc } from 'firebase/firestore';
import { db } from './firebase';
import type { Brand } from './types';
import type { FeedStory } from './feed-cache';
import './video-builder.css';
import './approved-ncpn.css';
import './story-image.css';
import './scene-layout.css';
import './storyboard.css';

const appealsStoryboard = [
  ['Power shift upheld', 'The North Carolina Court of Appeals upheld the law shifting elections-board appointment power from the governor to State Auditor Dave Boliek.'],
  ['A 2–1 decision', 'The ruling reversed an earlier trial-court decision that had found the law unconstitutional.'],
  ['State + 100 county boards', 'Boliek keeps appointment power over the State Board of Elections and every county elections board.'],
  ['Not a blanket rule', 'The court said future transfers of power must still be judged case by case.'],
  ['A dissenting view', 'One judge said the change strips the governor of constitutional authority over election laws.'],
];

export function VideoBuilder({ brand, story, packageId, onClose }: { brand: Brand; story: FeedStory; packageId: string; onClose: () => void }) {
  const hasAppealsStoryboard = story.id === 'appeals-court-election-power';
  const [format, setFormat] = useState('News update');
  const [script, setScript] = useState(hasAppealsStoryboard ? 'North Carolina’s Appeals Court has upheld the law shifting elections-board appointment power to State Auditor Dave Boliek.\n\nThe court ruled 2 to 1, reversing an earlier decision that found the change unconstitutional.\n\nThe ruling leaves Boliek in control of appointments to the State Board of Elections and all 100 county boards.\n\nThe court said this does not settle every future power-transfer dispute. Those cases must be decided individually.\n\nA dissenting judge said the law strips the governor of constitutional authority over election laws. Read the full story at ncpoliticalnews.com.' : `${story.title}. ${story.description} Read the full story at ${brand.site?.replace(/^https?:\/\//, '') || brand.name}.`);
  const [visualText, setVisualText] = useState(story.description.split(/(?<=[.!?])\s/)[0] || story.description);
  const [saved, setSaved] = useState(false);
  const [activeScene, setActiveScene] = useState(0);
  const save = async (ready = false) => { await updateDoc(doc(db, 'packages', packageId), { format, script, visualText, status: ready ? 'review' : 'drafting', updatedAt: serverTimestamp() }); setSaved(true); };
  return <main className="builder" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}>
    <header className="builder-top"><button onClick={onClose}>← Story desk</button><p>{brand.name} · video package</p><a href={story.link} target="_blank" rel="noreferrer">Read original ↗</a></header>
    <section className="builder-main"><div className="builder-copy"><p className="eyebrow">Step 1 of 3 · Shape the story</p><h1>{story.title}</h1><p className="source-summary">{story.description}</p>{hasAppealsStoryboard && <section className="storyboard"><div><p className="eyebrow">Five-scene storyboard</p><h2>Select a scene to inspect its words.</h2></div><div className="scene-strip">{appealsStoryboard.map(([title, line], index) => <button key={title} onClick={() => setActiveScene(index)} className={`scene-tile ${activeScene === index ? 'selected' : ''}`}><span>Scene {index + 1}</span><div className="scene-image" style={{ backgroundImage: `url(${story.imageUrl})` }} /><h3>{title}</h3><p>{line}</p></button>)}</div></section>}<div className="format-choice"><p className="eyebrow">Video format</p>{['News update', 'Three things to know', 'Explainer', 'Quote-led'].map(item => <button key={item} className={format === item ? 'active' : ''} onClick={() => setFormat(item)}>{item}</button>)}</div><label className="script-field"><span>Spoken script</span><textarea value={script} onChange={event => setScript(event.target.value)} /><small>Make this sound like your newsroom—not like an AI wrote it.</small></label><label className="visual-field"><span>Scene 1 · on-screen support text</span><textarea value={visualText} onChange={event => setVisualText(event.target.value)} /><small>One concise thought that supports the spoken script. It is not a transcript.</small></label><div className="builder-actions"><button className="save-draft" onClick={() => save(false)}>Save draft</button><button className="send-review" onClick={() => save(true)}>Ready for visual design →</button>{saved && <span>Saved</span>}</div></div>
      <aside className="video-preview"><p className="eyebrow">Approved visual · Scene {activeScene + 1}</p><div className="phone approved scene"><div className="preview-top">{brand.logoUrl ? <img src={brand.logoUrl} alt={brand.name} /> : brand.name}</div><strong className="preview-headline">{hasAppealsStoryboard ? appealsStoryboard[activeScene][0] : story.title}</strong><div className="story-image-card">{story.imageUrl ? <img src={story.imageUrl} alt="Story lead visual" /> : <div><b>Lead image</b><span>Refresh stories to load</span></div>}</div><div className="lower-caption">{hasAppealsStoryboard ? appealsStoryboard[activeScene][1] : visualText}</div></div><p>Portrait story image, headline limited to two lines (three only when needed), and on-screen text that supports the voiceover.</p></aside>
    </section>
  </main>;
}
