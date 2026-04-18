import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';
import { auth } from '../firebase';
import { onAuthStateChanged, signOut, getIdToken } from 'firebase/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
            if (fbUser) {
                const idToken = await fbUser.getIdToken();
                setUser({
                    uid: fbUser.uid,
                    email: fbUser.email,
                    name: fbUser.displayName || fbUser.email.split('@')[0],
                    picture: fbUser.photoURL
                });
                setToken(idToken);
                localStorage.setItem('firebaseToken', idToken);
            } else {
                const storedToken = localStorage.getItem('firebaseToken');
                if (storedToken) {
                    localStorage.removeItem('firebaseToken');
                }
                setUser(null);
                setToken(null);
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    const logout = async () => {
        try {
            await signOut(auth);
            localStorage.removeItem('firebaseToken');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    const isAuthenticated = !!user;

    if (loading) {
        return (
            <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
                <div className="text-zinc-400 text-sm">Loading...</div>
            </div>
        );
    }

    return (
        <AuthContext.Provider value={{ user, token, logout, isAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
