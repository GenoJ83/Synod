import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Brain, Mail, Lock, User, Eye, EyeOff, Loader2, ArrowLeft, Sun, Moon, ChevronRight, CheckCircle2 } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Signup = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { theme, toggleTheme } = useTheme();
    const { login } = useAuth();

    const handleSignup = async (e) => {
        e.preventDefault();
        setLoading(true);
        // Simulate auth
        setTimeout(() => {
            const userData = { email, name };
            login(userData);
            setLoading(false);
            navigate('/dashboard');
        }, 1500);
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
                </div>

                <p className="mt-8 text-center text-app-muted text-xs font-medium">
                    Synod uses bank-grade encryption to protect your lecture data.
                </p>
            </motion.div>
        </div>
    );
};

export default Signup;
