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
        );
    }

    if (currentStep === 3) {
        const percentage = Math.round((score / totalQuestions) * 100);
        return (
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-12 text-center shadow-xl max-w-2xl mx-auto animate-fade-in">
                <div className="relative w-32 h-32 mx-auto mb-8">
                    <svg className="w-full h-full transform -rotate-90">
                        <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-zinc-800" />
                        <circle
                            cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="8" fill="transparent"
                            strokeDasharray={364.4}
                            strokeDashoffset={364.4 - (percentage / 100) * 364.4}
                            className="text-zinc-100 transition-all duration-1000 ease-out"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center text-2xl font-black text-white">
                        {percentage}%
                    </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Session Complete</h3>
                <p className="text-zinc-500 mb-10 text-lg">You correctly answered {score} of {totalQuestions} questions.</p>

                <div className="grid grid-cols-2 gap-4">
                    <button
                        onClick={onReset}
                        className="py-3 bg-zinc-800 hover:bg-zinc-700 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                    >
                        <RotateCcw className="w-4 h-4" /> Reset
                    </button>
                    <button
                        className="py-3 bg-zinc-100 hover:bg-white text-zinc-950 font-bold rounded-xl transition-all"
                        onClick={() => {
                            setCurrentStep(0);
                            setScore(0);
                            setMcqIndex(0);
                            setFibIndex(0);
                        }}
                    >
                        Retake
                    </button>
                </div>
            </div>
        );
    }

    const currentQuestion = currentStep === 1 ? mcqs[mcqIndex] : fibs[fibIndex];
    const progress = ((mcqIndex + (currentStep === 2 ? mcqs.length : 0) + fibIndex) / totalQuestions) * 100;

    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 md:p-12 shadow-xl max-w-3xl mx-auto relative overflow-hidden animate-fade-in">
            <div className="absolute top-0 left-0 w-full h-1 bg-zinc-800">
                <div className="h-full bg-zinc-100 transition-all duration-500" style={{ width: `${progress}%` }} />
            </div>

            <div className="flex justify-between items-center mb-10">
                <span className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Q {mcqIndex + (currentStep === 2 ? mcqs.length : 0) + fibIndex + 1} / {totalQuestions}</span>
                <span className="px-2 py-0.5 bg-zinc-800 border border-zinc-700 rounded text-[9px] font-bold text-zinc-400 uppercase tracking-widest">
                    {currentStep === 1 ? 'Multiple Choice' : 'Critical Recall'}
                </span>
            </div>

            <h4 className="text-xl md:text-2xl font-bold text-zinc-100 mb-10 leading-relaxed">
                {currentQuestion.question}
            </h4>

            <div className="space-y-3">
                {currentStep === 1 ? (
                    mcqs[mcqIndex].options.map((option, i) => (
                        <button
                            key={i}
                            onClick={() => handleMcqSubmit(option)}
                            className={cn(
                                "w-full p-4 rounded-xl border text-left transition-all text-sm font-medium",
                                selectedOption === option
                                    ? isCorrect ? 'bg-emerald-950/20 border-emerald-500 text-emerald-500' : 'bg-red-950/20 border-red-500 text-red-500'
                                    : showFeedback && option === currentQuestion.answer
                                        ? 'bg-emerald-950/20 border-emerald-500 text-emerald-500'
                                        : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-600'
                            )}
                            disabled={showFeedback}
                        >
                            <div className="flex items-center justify-between">
                                <span>{option}</span>
                                {showFeedback && option === currentQuestion.answer && <CheckCircle2 className="w-4 h-4" />}
                                {showFeedback && selectedOption === option && !isCorrect && <XCircle className="w-4 h-4" />}
                            </div>
                        </button>
                    ))
                ) : (
                    <div className="space-y-4">
                        <input
                            type="text"
                            autoFocus
                            value={fibAnswer}
                            onChange={(e) => setFibAnswer(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleFibSubmit()}
                            placeholder="Identify the concept..."
                            className={cn(
                                "w-full p-4 rounded-xl bg-zinc-950 border transition-all outline-none text-sm font-medium",
                                showFeedback
                                    ? isCorrect ? 'border-emerald-500 text-emerald-500' : 'border-red-500 text-red-500'
                                    : 'border-zinc-800 text-zinc-100 focus:border-zinc-500'
                            )}
                            disabled={showFeedback}
                        />
                        {!showFeedback && (
                            <button
                                onClick={handleFibSubmit}
                                className="w-full bg-zinc-100 text-zinc-950 py-3 rounded-lg font-bold text-sm"
                            >
                                Submit
                            </button>
                        )}
                    </div>
                )}
            </div>

            <AnimatePresence>
                {showFeedback && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-10 pt-8 border-t border-zinc-800/50 flex items-center justify-between"
                    >
                        <div className={cn(
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
        </div>
    );
};

export default QuizSection;
