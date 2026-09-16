import { useEffect, useState, type CSSProperties } from 'react';
import { GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut, type User } from 'firebase/auth';
import { collection, doc, getDoc, onSnapshot, serverTimestamp, setDoc } from 'firebase/firestore';
import { auth, db } from './firebase';
import { starterBrands } from './seed';
import type { Brand, TeamUser, VideoPackage } from './types';

const people = ['Kristy Kelly', 'BJ Murphy', 'Aleatha Thrower', 'Trey Scott', 'Destiny Stout', 'Danny Perez', 'Katy Keenan'];

function Login() { return <main className="login"><p className="eyebrow">Magic Mile Media</p><h1>Local Voice<br />Engine</h1><p>A private studio for making your reporting move.</p><button onClick={() => signInWithPopup(auth, new GoogleAuthProvider())}>Continue with Google</button><small>Team access only</small></main>; }

export function App() {
  const [user, setUser] = useState<User | null>(null); const [profile, setProfile] = useState<TeamUser | null>(null);
  const [brands, setBrands] = useState<Brand[]>([]); const [packages, setPackages] = useState<VideoPackage[]>([]); const [activeBrand, setActiveBrand] = useState<string>('neuse-news');
  useEffect(() => onAuthStateChanged(auth, async account => { setUser(account); if (account) { const ref = doc(db, 'users', account.uid); const current = await getDoc(ref); if (!current.exists()) await setDoc(ref, { name: account.displayName || account.email?.split('@')[0], email: account.email, role: 'user', active: false, createdAt: serverTimestamp() }); setProfile({ id: account.uid, ...(await getDoc(ref)).data() } as TeamUser); } else setProfile(null); }), []);
  useEffect(() => { if (!user) return; return onSnapshot(collection(db, 'brands'), s => setBrands(s.docs.map(x => x.data() as Brand))); }, [user]);
  useEffect(() => { if (!user) return; return onSnapshot(collection(db, 'packages'), s => setPackages(s.docs.map(x => x.data() as VideoPackage))); }, [user]);
  if (!user || !profile) return <Login />;
  if (!profile.active) return <main className="login"><p className="eyebrow">Local Voice Engine</p><h1>Access requested.</h1><p>Your account is waiting for a newsroom administrator to approve it.</p><button onClick={() => signOut(auth)}>Use another account</button></main>;
  const visibleBrands = brands.length ? brands : starterBrands; const brand = visibleBrands.find(x => x.id === activeBrand) || visibleBrands[0]; const stories = packages.filter(x => x.brandId === brand.id);
  return <main className="shell" style={{ '--brand': brand.colors.primary, '--accent': brand.colors.accent } as CSSProperties}>
    <aside><div className="mark"><span>MM</span><strong>Local Voice<br/>Engine</strong></div><nav><button className="selected">Studio</button><button>Library</button><button>Templates</button><button>Activity</button></nav><div className="profile"><b>{profile.name}</b><small>{profile.role}</small><button onClick={() => signOut(auth)}>Sign out</button></div></aside>
    <section className="content"><header><div><p className="eyebrow">{brand.name}</p><h1>Today’s studio</h1></div><button className="new">+ New package</button></header><div className="brand-rail">{visibleBrands.map(item => <button key={item.id} onClick={() => setActiveBrand(item.id)} className={item.id === brand.id ? 'brand active' : 'brand'} style={{ '--chip': item.colors.primary } as CSSProperties}>{item.name}</button>)}</div><section className="hero"><div><p className="eyebrow">Ready to make</p><h2>Turn a story into<br/>a video people stop for.</h2><p>One voice. One point of view. Built for the way your newsroom actually works.</p><button className="new">Choose a story</button></div><div className="reel"><div className="reel-image"/><span>{brand.name}</span><strong>Stories worth<br/>stopping for.</strong><small>Local Voice Engine</small></div></section><section className="section-head"><div><p className="eyebrow">In progress</p><h2>Your packages</h2></div><button className="quiet">View library →</button></section><section className="cards">{stories.length ? stories.map(story => <article key={story.id}><div className="card-art"/><p>{story.status}</p><h3>{story.headline}</h3><small>{people.includes(story.assignedTo || '') ? story.assignedTo : 'Unassigned'}</small></article>) : <article className="empty"><span>✦</span><h3>No packages in this brand yet.</h3><p>Start with a story, then choose a visual format.</p><button className="new">Create first package</button></article>}</section></section>
  </main>;
}
