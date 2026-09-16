import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const app = initializeApp({
  apiKey: 'AIzaSyD2RqDXbHoe_sE2P56EX28CUQM4PaTIqS0',
  authDomain: 'local-voice-engine-kdb.firebaseapp.com',
  projectId: 'local-voice-engine-kdb',
  storageBucket: 'local-voice-engine-kdb.firebasestorage.app',
  messagingSenderId: '122567418383',
  appId: '1:122567418383:web:1c28588446e86f075b797a',
});
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);
