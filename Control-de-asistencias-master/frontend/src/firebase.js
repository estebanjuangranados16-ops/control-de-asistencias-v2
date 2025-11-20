import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyAg1Ow6dA61tnx0TBjU48tLRgSe2Qvb170",
  authDomain: "control-de-asistencias-4654d.firebaseapp.com",
  projectId: "control-de-asistencias-4654d",
  storageBucket: "control-de-asistencias-4654d.firebasestorage.app",
  messagingSenderId: "758990998123",
  appId: "1:758990998123:web:dee65a779451eff6e2bf2e",
  measurementId: "G-MJS0NE72B8"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const analytics = getAnalytics(app);
export default app;