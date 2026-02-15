import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

const API_BASE_URL = 'http://localhost:8000';

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(() => {
        return localStorage.getItem('synod_token') || null;
    });
    const [loading, setLoading] = useState(true);

    // Verify token on mount
    useEffect(() => {
        const verifyToken = async () => {
            const storedToken = localStorage.getItem('synod_token');
            if (!storedToken) {
                setLoading(false);
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/auth/verify`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ token: storedToken }),
                });

                if (response.ok) {
                    const data = await response.json();
                    setUser(data.user);
                    setToken(storedToken);
                } else {
                    // Token invalid, clear it
                    localStorage.removeItem('synod_token');
                    setToken(null);
                    setUser(null);
                }
            } catch (error) {
                console.error('Token verification failed:', error);
                localStorage.removeItem('synod_token');
                setToken(null);
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        verifyToken();
    }, []);

    const login = (userData) => {
        // Traditional email/password login (for future implementation)
        setUser(userData);
        // Note: In a real implementation, this would also receive a token from the backend
    };

    const loginWithToken = async (jwtToken) => {
        // Login with JWT token from OAuth callback
        try {
            const response = await fetch(`${API_BASE_URL}/auth/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: jwtToken }),
            });

            if (response.ok) {
                const data = await response.json();
                setUser(data.user);
                setToken(jwtToken);
                localStorage.setItem('synod_token', jwtToken);
            } else {
                throw new Error('Token verification failed');
            }
        } catch (error) {
            console.error('Login with token failed:', error);
            throw error;
        }
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('synod_token');
    };

    const isAuthenticated = !!user;

    if (loading) {
        // Optional: Return a loading spinner during initial verification
        return null;
    }

    return (
        <AuthContext.Provider value={{ user, token, login, loginWithToken, logout, isAuthenticated }}>
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
