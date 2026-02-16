import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Mail, Lock, User, Eye, EyeOff, Loader2, ArrowLeft, Sun, Moon, ChevronRight, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config';

const Signup = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const { login, isAuthenticated } = useAuth();

    React.useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    const handleOAuth = (provider) => {
        // Redirect to backend OAuth endpoint
        window.location.href = `${API_BASE_URL}/auth/${provider}/login`;
    };

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, full_name: name }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Registration failed');
            }

            const data = await response.json();
            login(data.user, data.token);
            navigate('/dashboard');
        } catch (error) {
            console.error('Signup error:', error);
            alert(error.message); // Simple alert for now, could be better UI
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-app-bg text-app-fg font-sans selection:bg-blue-500/30 transition-colors duration-300 flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-1/4 left-1/4 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full pointer-events-none" />

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
                        Already have an account? <button onClick={() => navigate('/login')} className="text-blue-500 font-bold hover:underline">Log in</button>
                    </span>
                </div>
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md relative z-10 py-12"
            >
                <div className="flex flex-col items-center mb-10">
                    <div className="w-16 h-16 bg-app-fg rounded-[2rem] flex items-center justify-center mb-6 shadow-2xl">
                        <Brain className="w-8 h-8 text-app-bg" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight mb-2">Create Account</h1>
                    <p className="text-app-muted text-center font-medium">Join 5,000+ students using Synod.</p>
                </div>

                <div className="pro-card p-8 bg-app-bg/40 backdrop-blur-xl border border-app-border">
                    <form onSubmit={handleSignup} className="space-y-6">
                        {/* ... existing form fields ... */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest ml-1">Full Name</label>
                            <div className="relative group">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type="text"
                                    required
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Alex Johnson"
                                    className="w-full pl-10 pr-4 py-3 pro-input text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest ml-1">Institutional Email</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="alex@university.edu"
                                    className="w-full pl-10 pr-4 py-3 pro-input text-sm"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-app-muted uppercase tracking-widest ml-1">Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-app-muted group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Create a strong password"
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
                            <div className="grid grid-cols-3 gap-2 mt-2 px-1">
                                <div className="h-1 bg-blue-500 rounded-full" />
                                <div className="h-1 bg-blue-500 rounded-full" />
                                <div className="h-1 bg-app-border rounded-full" />
                            </div>
                        </div>

                        <div className="flex items-start gap-3 px-1">
                            <div className="mt-1">
                                <CheckCircle2 className="w-4 h-4 text-blue-500" />
                            </div>
                            <p className="text-[10px] text-app-muted leading-relaxed">
                                I agree to the <span className="text-app-fg font-bold cursor-pointer">Terms of Service</span> and acknowledge the <span className="text-app-fg font-bold cursor-pointer">Privacy Policy</span>.
                            </p>
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
                                    Create Account
                                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 flex flex-col items-center gap-4">
                        <div className="flex items-center gap-4 w-full text-app-muted">
                            <div className="h-[1px] bg-app-border flex-1" />
                            <span className="text-[10px] uppercase font-bold tracking-widest shrink-0">Supported Methods</span>
                            <div className="h-[1px] bg-app-border flex-1" />
                        </div>
                        <div className="flex gap-4">
                            <button
                                onClick={() => handleOAuth('google')}
                                className="w-12 h-12 border border-app-border rounded-xl bg-app-card/50 flex items-center justify-center hover:bg-app-card hover:border-app-muted transition-all active:scale-95"
                                title="Continue with Google"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                                    <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-1 .67-2.28 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                    <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
                                    <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                </svg>
                            </button>
                            <button
                                onClick={() => handleOAuth('github')}
                                className="w-12 h-12 border border-app-border rounded-xl bg-app-card/50 flex items-center justify-center hover:bg-app-card hover:border-app-muted transition-all active:scale-95"
                                title="Continue with GitHub"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="currentColor" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                <p className="mt-8 text-center text-app-muted text-xs font-medium">
                    Synod uses bank-grade encryption to protect your lecture data.
                </p>
            </motion.div>
        </div>
    );
};

export default Signup;
