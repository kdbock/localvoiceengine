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
import './inline-edit.css';
import './fact-scene.css';

type Scene = { kind: 'image' | 'fact'; label: string; title: string; text: string };
const appealsStoryboard: Scene[] = [
  { kind: 'image', label: 'Opening story card', title: 'Court upholds power shift', text: 'Elections-board appointment power stays with State Auditor Dave Boliek.' },
  { kind: 'fact', label: 'What changed', title: 'Auditor keeps appointment power', text: 'The ruling leaves Boliek in control of appointments to the State Board of Elections and all 100 county boards.' },
  { kind: 'fact', label: 'The ruling', title: 'Court rules 2–1', text: 'The Appeals Court reversed an earlier trial-court decision that found the law unconstitutional.' },
  { kind: 'fact', label: 'Why it matters', title: 'Every county board is affected', text: 'Appointments have shifted the State Board and county boards to Republican majorities.' },
  { kind: 'fact', label: 'What happens next', title: 'Future cases stand on their own', text: 'The court said future transfers of power must still be decided case by case.' },
];

export function VideoBuilder({ brand, story, packageId, onClose }: { brand: Brand; story: FeedStory; packageId: string; onClose: () => void }) {
  const hasAppealsStoryboard = story.id === 'appeals-court-election-power';
  const [format, setFormat] = useState('News update');
  const [script, setScript] = useState(hasAppealsStoryboard ? 'North Carolina’s Appeals Court has upheld the law shifting elections-board appointment power to State Auditor Dave Boliek.\n\nThe ruling leaves Boliek in control of appointments to the State Board of Elections and all 100 county boards.\n\nThe court ruled 2 to 1, reversing an earlier decision that found the change unconstitutional.\n\nThe ruling has already shifted the State Board and county boards to Republican majorities.\n\nThe court said future power-transfer disputes must be decided case by case. Read the full story at ncpoliticalnews.com.' : `${story.title}. ${story.description} Read the full story at ${brand.site?.replace(/^https?:\/\//, '') || brand.name}.`);
  const [visualText, setVisualText] = useState(story.description.split(/(?<=[.!?])\s/)[0] || story.description);
  const [saved, setSaved] = useState(false); const [activeScene, setActiveScene] = useState(0); const [scenes, setScenes] = useState(appealsStoryboard);
  const updateScene = (part: 'title' | 'text', value: string) => setScenes(current => current.map((scene, index) => index === activeScene ? { ...scene, [part]: value } : scene));
  const save = async (ready = false) => { await updateDoc(doc(db, 'packages', packageId), { format, script, visualText, ...(hasAppealsStoryboard ? { scenes } : {}), status: ready ? 'review' : 'drafting', updatedAt: serverTimestamp() }); setSaved(true); };
  const scene = hasAppealsStoryboard ? scenes[activeScene] : null;
  return <main className="builder" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}>
    <header className="builder-top"><button onClick={onClose}>← Story desk</button><p>{brand.name} · video package</p><a href={story.link} target="_blank" rel="noreferrer">Read original ↗</a></header>
    <section className="builder-main"><div className="builder-copy"><p className="eyebrow">Step 1 of 3 · Shape the story</p><h1>{story.title}</h1><p className="source-summary">{story.description}</p>{hasAppealsStoryboard && <section className="storyboard"><div><p className="eyebrow">Five-scene storyboard</p><h2>Distinct editorial beats, not repeated cards.</h2></div><div className="scene-strip">{scenes.map((item, index) => <button key={`${item.title}-${index}`} onClick={() => setActiveScene(index)} className={`scene-tile ${item.kind} ${activeScene === index ? 'selected' : ''}`}><span>Scene {index + 1} · {item.kind === 'image' ? 'Image' : 'Fact'}</span><div className="scene-image" style={item.kind === 'image' ? { backgroundImage: `url(${story.imageUrl})` } : undefined} /><h3>{item.title}</h3><p>{item.text}</p></button>)}</div></section>}<div className="format-choice"><p className="eyebrow">Video format</p>{['News update', 'Three things to know', 'Explainer', 'Quote-led'].map(item => <button key={item} className={format === item ? 'active' : ''} onClick={() => setFormat(item)}>{item}</button>)}</div><label className="script-field"><span>Spoken script</span><textarea value={script} onChange={event => setScript(event.target.value)} /><small>Make this sound like your newsroom—not like an AI wrote it.</small></label><label className="visual-field"><span>Fallback on-screen support text</span><textarea value={visualText} onChange={event => setVisualText(event.target.value)} /><small>Storyboards use their scene-specific text above.</small></label><div className="builder-actions"><button className="save-draft" onClick={() => save(false)}>Save draft</button><button className="send-review" onClick={() => save(true)}>Ready for visual design →</button>{saved && <span>Saved</span>}</div></div>
      <aside className="video-preview"><p className="eyebrow">Approved visual · Scene {activeScene + 1}</p><div className={`phone approved scene ${scene?.kind === 'fact' ? 'fact-scene' : 'image-scene'}`}><div className="preview-top">{brand.logoUrl ? <img src={brand.logoUrl} alt={brand.name} /> : brand.name}</div>{scene?.kind === 'image' && <><strong className="preview-headline editable" contentEditable suppressContentEditableWarning onInput={event => updateScene('title', event.currentTarget.textContent || '')}>{scene.title}</strong><div className="story-image-card">{story.imageUrl ? <img src={story.imageUrl} alt="Story lead visual" /> : <div><b>Lead image</b><span>Refresh stories to load</span></div>}</div><div className="lower-caption editable" contentEditable suppressContentEditableWarning onInput={event => updateScene('text', event.currentTarget.textContent || '')}>{scene.text}</div></>}{scene?.kind === 'fact' && <div className="fact-panel"><span>{scene.label}</span><strong className="editable" contentEditable suppressContentEditableWarning onInput={event => updateScene('title', event.currentTarget.textContent || '')}>{scene.title}</strong><p className="editable" contentEditable suppressContentEditableWarning onInput={event => updateScene('text', event.currentTarget.textContent || '')}>{scene.text}</p><i /></div>}{!scene && <div className="lower-caption">{visualText}</div>}<small className="read-more">Read the full story at ncpoliticalnews.com</small></div><p>Scene 1 uses the story image. Scenes 2–5 are separate fact panels, with their own editable copy and transitions in the final render.</p></aside>
    </section>
  </main>;
}
