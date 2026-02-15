import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const AuthCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { loginWithToken } = useAuth();
    const [status, setStatus] = useState('loading'); // loading, success, error

    useEffect(() => {
        const handleCallback = async () => {
            const token = searchParams.get('token');
            const error = searchParams.get('error');

            if (error) {
                setStatus('error');
                setTimeout(() => navigate('/login'), 3000);
                return;
            }

            if (!token) {
                setStatus('error');
                setTimeout(() => navigate('/login'), 3000);
                return;
            }

            try {
                // Verify and store the token
                await loginWithToken(token);
                setStatus('success');
                setTimeout(() => navigate('/dashboard'), 1500);
            } catch (err) {
                console.error('Auth callback error:', err);
                setStatus('error');
                setTimeout(() => navigate('/login'), 3000);
            }
        };

        handleCallback();
    }, [searchParams, navigate, loginWithToken]);

    return (
        <div className="min-h-screen bg-app-bg text-app-fg flex items-center justify-center p-6">
            <div className="pro-card p-12 max-w-md w-full text-center">
                {status === 'loading' && (
                    <>
                        <Loader2 className="w-16 h-16 mx-auto mb-4 animate-spin text-blue-500" />
                        <h2 className="text-2xl font-bold mb-2">Signing you in...</h2>
                        <p className="text-app-muted">Please wait while we complete your authentication.</p>
                    </>
                )}

                {status === 'success' && (
                    <>
                        <CheckCircle2 className="w-16 h-16 mx-auto mb-4 text-green-500" />
                        <h2 className="text-2xl font-bold mb-2">Success!</h2>
                        <p className="text-app-muted">Redirecting to your dashboard...</p>
                    </>
                )}

                {status === 'error' && (
                    <>
                        <XCircle className="w-16 h-16 mx-auto mb-4 text-red-500" />
                        <h2 className="text-2xl font-bold mb-2">Authentication Failed</h2>
                        <p className="text-app-muted">Redirecting to login page...</p>
                    </>
                )}
            </div>
        </div>
    );
};

export default AuthCallback;
