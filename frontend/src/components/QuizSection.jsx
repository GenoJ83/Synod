import React, { useState } from 'react';
import { CheckCircle2, XCircle, ChevronRight, HelpCircle, RotateCcw, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const QuizSection = ({ quiz, onReset }) => {
    const [currentStep, setCurrentStep] = useState(0); // 0: intro, 1: mcqs, 2: fibs, 3: result
    const [mcqIndex, setMcqIndex] = useState(0);
    const [fibIndex, setFibIndex] = useState(0);
    const [score, setScore] = useState(0);
    const [selectedOption, setSelectedOption] = useState(null);
    const [fibAnswer, setFibAnswer] = useState('');
    const [showFeedback, setShowFeedback] = useState(false);
    const [isCorrect, setIsCorrect] = useState(false);

    const mcqs = quiz.mcqs || [];
    const fibs = quiz.fill_in_the_blanks || [];
    const totalQuestions = mcqs.length + fibs.length;

    const handleMcqSubmit = (option) => {
        if (showFeedback) return;
        setSelectedOption(option);
        const correct = option === mcqs[mcqIndex].answer;
        setIsCorrect(correct);
        if (correct) setScore(score + 1);
        setShowFeedback(true);
    };

    const nextQuestion = () => {
        setShowFeedback(false);
        setSelectedOption(null);
        setFibAnswer('');

        if (currentStep === 1) {
            if (mcqIndex < mcqs.length - 1) {
                setMcqIndex(mcqIndex + 1);
            } else if (fibs.length > 0) {
                setCurrentStep(2);
            } else {
                setCurrentStep(3);
            }
        } else if (currentStep === 2) {
            if (fibIndex < fibs.length - 1) {
                setFibIndex(fibIndex + 1);
            } else {
                setCurrentStep(3);
            }
        }
    };

    const handleFibSubmit = () => {
        if (showFeedback) return;
        const correct = fibAnswer.toLowerCase().trim() === fibs[fibIndex].answer.toLowerCase().trim();
        setIsCorrect(correct);
        if (correct) setScore(score + 1);
        setShowFeedback(true);
    };

    if (currentStep === 0) {
        return (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center shadow-xl max-w-2xl mx-auto animate-fade-in">
                <div className="w-16 h-16 bg-zinc-800 border border-zinc-700 rounded-2xl flex items-center justify-center mx-auto mb-8 text-zinc-400">
                    <HelpCircle className="w-8 h-8" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">Knowledge Assessment</h3>
                <p className="text-zinc-500 mb-10 text-lg leading-relaxed">
                    Test your understanding with {totalQuestions} generated questions.
                </p>
                <button
                    onClick={() => setCurrentStep(mcqs.length > 0 ? 1 : 2)}
                    className="w-full bg-zinc-100 hover:bg-white text-zinc-950 py-4 rounded-xl font-bold text-sm transition-all shadow-sm"
                >
                    Begin Quiz
                </button>
            </div>
        if (currentQuestion < quizData.length - 1) {
            setCurrentQuestion(prev => prev + 1);
            setSelectedAnswer(null);
        } else {
            setShowResults(true);
        }
    };

    const resetQuiz = () => {
        setCurrentQuestion(0);
        setSelectedAnswer(null);
        setShowResults(false);
        setScore(0);
    };

    if (showResults) {
        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="pro-card p-12 text-center"
            >
                <div className="w-20 h-20 bg-blue-500/10 text-blue-500 rounded-[2rem] flex items-center justify-center mx-auto mb-8">
                    <Trophy className="w-10 h-10" />
                </div>
                <h3 className="text-3xl font-bold mb-2">Synthesis Complete</h3>
                <p className="text-app-muted mb-8 italic">"You've mastered the core concepts of this lecture."</p>

                <div className="flex justify-center gap-12 mb-12">
                    <div>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-widest mb-1">Score</p>
                        <p className="text-4xl font-bold text-blue-500">{Math.round((score / quizData.length) * 100)}%</p>
                    </div>
                    <div className="w-[1px] bg-app-border" />
                    <div>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-widest mb-1">Correct</p>
                        <p className="text-4xl font-bold">{score}/{quizData.length}</p>
                    </div>
                </div>

                <div className="flex gap-4">
                    <button
                        onClick={resetQuiz}
                        className="flex-1 py-4 bg-app-card border border-app-border rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-app-bg transition-all"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Retake Assessment
                    </button>
                    <button className="flex-1 py-4 bg-app-fg text-app-bg rounded-2xl font-bold shadow-xl hover:opacity-90 transition-all">
                        Download Report
                    </button>
                </div>
            </motion.div>
        );
    }

    const question = quizData[currentQuestion];

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-app-card border border-app-border rounded-lg flex items-center justify-center text-app-muted">
                        <HelpCircle className="w-4 h-4" />
                    </div>
                    <div>
                        <h3 className="text-xs font-bold uppercase tracking-widest">Knowledge Check</h3>
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-tighter">Question {currentQuestion + 1} of {quizData.length}</p>
                    </div>
                </div>
                <div className="flex gap-1">
                    {quizData.map((_, i) => (
                        <div
                            key={i}
                            "flex items-center gap-3 font-bold text-xs uppercase tracking-widest",
                        isCorrect ? 'text-emerald-500' : 'text-red-500'
                    )}>
                    {isCorrect ? <Award className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                    <span>{isCorrect ? 'Correct Perception' : `Reference Answer: ${currentQuestion.answer}`}</span>
                </div>
                <button
                    onClick={nextQuestion}
                    className="bg-zinc-800 hover:bg-zinc-700 p-2 rounded-lg transition-colors"
                >
                    <ChevronRight className="w-5 h-5" />
                </button>
            </motion.div>
                )}
        </AnimatePresence>
        </div >
    );
};

export default QuizSection;
