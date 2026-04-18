import React, { createContext, useContext, useState, useEffect } from 'react';
// Auth context for Firebase authentication
import { API_BASE_URL } from '../config';
import { auth, getRedirectResult, onAuthStateChanged, logout } from '../firebase';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initAuth = async () => {
            try {
                const result = await getRedirectResult(auth);
                if (result) {
                    const idToken = await result.user.getIdToken();
                    setUser({
                        uid: result.user.uid,
                        email: result.user.email,
                        name: result.user.displayName || result.user.email.split('@')[0],
                        picture: result.user.photoURL
                    });
                    setToken(idToken);
                    localStorage.setItem('firebaseToken', idToken);
                }
            } catch (error) {
                console.error('Redirect result error:', error);
            }

            const unsubscribe = onAuthStateChanged(async (fbUser) => {
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
        };

        initAuth();
    }, []);

    const handleLogout = async () => {
        try {
            await logout();
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
        <AuthContext.Provider value={{ user, token, logout: handleLogout, isAuthenticated }}>
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
