import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyCUumevI0pyU0rLiGEbQNzgnfQiZO95hRU",
  authDomain: "synod-3ce73.firebaseapp.com",
  projectId: "synod-3ce73",
  storageBucket: "synod-3ce73.firebasestorage.app",
  messagingSenderId: "643491590857",
  appId: "1:643491590857:web:b5f1c2757b0b0c131e9318",
  measurementId: "G-P95SHTDLG6"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
