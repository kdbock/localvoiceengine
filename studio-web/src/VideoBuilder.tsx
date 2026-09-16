import { useState, type CSSProperties } from 'react';
import { doc, serverTimestamp, updateDoc } from 'firebase/firestore';
import { db } from './firebase';
import type { Brand } from './types';
import type { FeedStory } from './feed-cache';
import './storyboard-builder.css';

type Scene = { label: string; voiceover: string; visualText: string; animation: string; approved: boolean; kind: 'image' | 'fact' };
const initialAppealsScenes: Scene[] = [
  { label: 'Power shift upheld', voiceover: 'North Carolina’s Appeals Court has upheld the law shifting elections-board appointment power to State Auditor Dave Boliek.', visualText: 'Auditor keeps elections-board appointment power.', animation: 'Slow editorial drift', approved: false, kind: 'image' },
  { label: 'What changed', voiceover: 'The ruling leaves Boliek in control of appointments to the State Board of Elections and all 100 county boards.', visualText: 'State board + all 100 county boards', animation: 'Card rise', approved: false, kind: 'fact' },
  { label: 'The ruling', voiceover: 'The court ruled 2 to 1, reversing an earlier decision that found the law unconstitutional.', visualText: 'Appeals Court rules 2–1', animation: 'Diagonal sweep', approved: false, kind: 'fact' },
  { label: 'Why it matters', voiceover: 'The ruling has already shifted the State Board and county boards to Republican majorities.', visualText: 'Board control has shifted statewide.', animation: 'Soft pulse', approved: false, kind: 'fact' },
  { label: 'What happens next', voiceover: 'The court said future power-transfer disputes must be decided case by case.', visualText: 'Future cases will be judged individually.', animation: 'Card rise', approved: false, kind: 'fact' },
];
const animations = ['Slow editorial drift', 'Diagonal sweep', 'Card rise', 'Soft pulse'];

export function VideoBuilder({ brand, story, packageId, onClose }: { brand: Brand; story: FeedStory; packageId: string; onClose: () => void }) {
  const isAppeals = story.id === 'appeals-court-election-power';
  const [scenes, setScenes] = useState<Scene[]>(isAppeals ? initialAppealsScenes : [{ label: 'Story opener', voiceover: story.description, visualText: story.title, animation: 'Slow editorial drift', approved: false, kind: 'image' }]);
  const [active, setActive] = useState(0); const [notice, setNotice] = useState(''); const scene = scenes[active];
  const change = (key: keyof Scene, value: string | boolean) => setScenes(current => current.map((item, index) => index === active ? { ...item, [key]: value } : item));
  const approve = async () => { change('approved', true); const next = scenes.map((item, index) => index === active ? { ...item, approved: true } : item); await updateDoc(doc(db, 'packages', packageId), { scenes: next, status: 'drafting', updatedAt: serverTimestamp() }); setNotice(`Scene ${active + 1} approved.`); };
  const compile = async () => { if (!scenes.every(item => item.approved)) return setNotice('Approve every scene before compiling.'); await updateDoc(doc(db, 'packages', packageId), { scenes, renderManifest: { aspectRatio: '9:16', scenes, compiledAt: new Date().toISOString() }, status: 'rendering', updatedAt: serverTimestamp() }); setNotice('Scenes compiled into the render package.'); };
  return <main className="storyboard-builder" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}>
    <header className="builder-bar"><button onClick={onClose}>← Story desk</button><div><p>{brand.name} · storyboard</p><strong>{story.title}</strong></div><a href={story.link} target="_blank" rel="noreferrer">Original story ↗</a></header>
    <main className="storyboard-workspace"><aside className="scene-nav"><p className="eyebrow">Storyboard</p>{scenes.map((item, index) => <button key={index} onClick={() => { setActive(index); setNotice(''); }} className={active === index ? 'active' : ''}><span>Scene {index + 1}</span><strong>{item.label}</strong><i>{item.approved ? 'Approved' : 'Needs review'}</i></button>)}<button className="compile" onClick={compile}>Compile scenes →</button>{notice && <p className="notice">{notice}</p>}</aside>
      <section className="scene-editor"><p className="eyebrow">Scene {active + 1} of {scenes.length}</p><label>Label<input value={scene.label} onChange={event => change('label', event.target.value)} /></label><label>Voiceover text<textarea value={scene.voiceover} onChange={event => change('voiceover', event.target.value)} /></label><label>Visual text<input value={scene.visualText} onChange={event => change('visualText', event.target.value)} /></label><label>Background animation<select value={scene.animation} onChange={event => change('animation', event.target.value)}>{animations.map(item => <option key={item}>{item}</option>)}</select></label><button className="approve" onClick={approve}>{scene.approved ? '✓ Scene approved' : 'Approve this scene'}</button></section>
      <section className={`scene-preview animation-${scene.animation.toLowerCase().replaceAll(' ', '-')}`}><p className="eyebrow">Live scene preview</p><div className={`reel-scene ${scene.kind}`}><div className="scene-brand">{brand.logoUrl ? <img src={brand.logoUrl} alt={brand.name} /> : brand.name}</div><h2>{scene.label}</h2>{scene.kind === 'image' ? <div className="scene-photo">{story.imageUrl && <img src={story.imageUrl} alt="Article lead" />}</div> : <div className="scene-fact"><span>{scene.label}</span><strong>{scene.visualText}</strong></div>}<p className="scene-visual">{scene.visualText}</p><small>Read the full story at ncpoliticalnews.com</small></div><p className="preview-note">Preview updates as you type. The background animation choice will be carried into the compiled render.</p></section>
    </main>
  </main>;
}
