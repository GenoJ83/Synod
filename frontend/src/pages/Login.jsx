import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, Loader2, ArrowLeft, Sun, Moon, ChevronRight } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { loginWithEmail, signInWithGoogle, onAuthStateChanged } from '../firebase';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [initialAuthCheck, setInitialAuthCheck] = useState(true);
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { theme, toggleTheme } = useTheme();

    useEffect(() => {
        const unsubscribe = onAuthStateChanged((user) => {
            if (user) {
                navigate('/dashboard', { replace: true });
            } else {
                setInitialAuthCheck(false);
            }
        });
        return () => unsubscribe();
    }, [navigate]);

    useEffect(() => {
        if (searchParams.get('signedIn') === '1') {
            navigate('/dashboard', { replace: true });
        }
    }, [searchParams, navigate]);

    const handleOAuth = async (provider) => {
        setLoading(true);
        try {
            await signInWithGoogle();
        } catch (error) {
            console.error('OAuth error:', error);
            setLoading(false);
            if (error.code !== 'auth/popup-closed-by-user') {
                alert('Authentication failed. Please try again.');
            }
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await loginWithEmail(email, password);
            navigate('/dashboard', { replace: true });
        } catch (error) {
            console.error('Login error:', error);
            setLoading(false);
            const message = error.code === 'auth/invalid-credential' 
                ? 'Invalid email or password'
                : 'Login failed. Please check your connection.';
            alert(message);
        }
    };

    if (initialAuthCheck) {
        return (
            <div className="min-h-screen bg-app-bg flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans selection:bg-blue-500/30 transition-colors duration-300 flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full pointer-events-none" />

            {/* Header / Nav */}
            <div className="absolute top-8 left-8 right-8 flex justify-between items-center max-w-[1600px] mx-auto w-full">
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center gap-2 text-app-muted hover:text-app-fg transition-colors group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-sm font-bold uppercase tracking-widest">Back</span>
                </button>
                <div className="flex items-center gap-4">
                    <button
                        onClick={toggleTheme}
                        className="p-2 text-app-muted hover:text-app-fg rounded-lg transition-colors border border-app-border bg-app-bg/50 backdrop-blur-sm"
                        title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
                    >
                        {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                    </button>
                    <span className="text-sm text-app-muted">
                        Don't have an account? <button onClick={() => navigate('/signup')} className="text-blue-500 font-bold hover:underline">Sign up</button>
                    </span>
                </div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10"
            >
                <div className="flex flex-col items-center mb-10">
                    <img src="/logo.png" alt="Synod" className="w-16 h-16 mb-6 rounded-xl" />
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome Back</h1>
                    <p className="text-app-muted text-center font-medium">Continue your knowledge synthesis journey.</p>
                </div>

                <div className="pro-card p-8 bg-app-bg/40 backdrop-blur-xl border border-app-border">
                    <form onSubmit={handleLogin} className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest ml-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="name@university.edu"
                                    className="w-full pl-10 pr-4 py-3 pro-input text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center ml-1">
                                <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest">Password</label>
                                <button
                                    type="button"
                                    onClick={() => navigate('/forgot-password')}
                                    className="text-[10px] font-bold text-blue-500 hover:text-blue-400 uppercase tracking-widest"
                                >
                                    Forgot?
                                </button>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter your password"
                                    className="w-full pl-10 pr-12 py-3 pro-input text-sm"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-app-muted hover:text-app-fg"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-app-fg text-app-bg py-4 rounded-xl font-bold text-sm hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 group shadow-xl"
                        >
                            {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <>
                                    Log In to Synod
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 flex flex-col items-center gap-4">
                        <div className="flex items-center gap-4 w-full text-app-muted">
                            <div className="h-[1px] bg-app-border flex-1" />
                            <span className="text-[10px] uppercase font-bold tracking-widest shrink-0">or sign in with</span>
                            <div className="h-[1px] bg-app-border flex-1" />
                        </div>
                        <div className="flex gap-4">
                            <button
                                onClick={() => handleOAuth('google')}
                                className="w-12 h-12 border border-app-border rounded-xl bg-app-card/50 flex items-center justify-center hover:bg-app-card hover:border-app-muted transition-all active:scale-95 shadow-md"
                                title="Continue with Google"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.28 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <p className="mt-8 text-center text-app-muted text-xs font-medium">
                    By continuing, you agree to Synod's <br />
                    <span className="text-app-fg cursor-pointer hover:underline">Terms of Service</span> and <span className="text-app-fg cursor-pointer hover:underline">Privacy Policy</span>.
                </p>
            </motion.div>
        </div>
    );
};

export default Login;
