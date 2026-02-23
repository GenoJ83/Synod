import React from 'react';
import { CheckCircle2, Brain } from 'lucide-react';

function ResultsDisplay({ result, startQuiz }) {
    if (!result) return null;

    const totalQuestions = (result.quiz?.mcqs?.length || 0) +
        (result.quiz?.fill_in_the_blanks?.length || 0) +
        (result.quiz?.true_false?.length || 0) +
        (result.quiz?.comprehension?.length || 0);

    return (
        <div className="w-full xl:w-1/2 space-y-8 animate-fade-in pb-20">
            <div className="pro-card p-8">
                <div className="flex items-center gap-3 mb-6 text-emerald-500">
                    <CheckCircle2 className="w-5 h-5" />
                    <h3 className="text-sm font-bold uppercase tracking-widest">Executive Summary</h3>
                </div>
                <p className="text-app-fg text-lg leading-relaxed font-medium">
                    {result.summary}
                </p>
                {result.metrics?.compression_ratio && (
                    <div className="mt-4 pt-4 border-t border-app-border/30 flex flex-col gap-3">
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] font-bold text-app-muted uppercase tracking-widest min-w-[80px]">Efficiency:</span>
                            <div className="flex-1 h-1 bg-app-card rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-emerald-500"
                                    style={{ width: `${Math.min(100, result.metrics.compression_ratio * 100)}%` }}
                                />
                            </div>
                            <span className="text-[10px] font-bold text-emerald-500">{(result.metrics.compression_ratio * 100).toFixed(1)}%</span>
                        </div>
                        {result.metrics?.coverage_score !== undefined && (
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-app-muted uppercase tracking-widest min-w-[80px]">Precision:</span>
                                <div className="flex-1 h-1 bg-app-card rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-blue-500"
                                        style={{ width: `${Math.min(100, result.metrics.coverage_score * 100)}%` }}
                                    />
                                </div>
                                <span className="text-[10px] font-bold text-blue-500">{(result.metrics.coverage_score * 100).toFixed(1)}%</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {result.takeaways && result.takeaways.length > 0 && (
                <div className="pro-card p-8">
                    <div className="flex items-center gap-3 mb-6 text-blue-500">
                        <Brain className="w-5 h-5" />
                        <h3 className="text-sm font-bold uppercase tracking-widest">Key Takeaways</h3>
                    </div>
                    <ul className="space-y-4">
                        {result.takeaways.map((takeaway, idx) => (
                            <li key={idx} className="flex gap-4 group">
                                <span className="text-blue-500 font-bold shrink-0">{idx + 1}.</span>
                                <p className="text-app-fg text-base font-medium leading-relaxed group-hover:text-blue-500 transition-colors">
                                    {takeaway}
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="bg-app-fg text-app-bg rounded-xl p-8 flex flex-col items-center justify-center text-center shadow-xl">
                <Brain className="w-10 h-10 mb-4 opacity-80" />
                <h3 className="text-xl font-bold mb-2">Knowledge Check</h3>
                <p className="text-app-bg/70 text-sm mb-6 font-medium">
                    Generated {totalQuestions} questions for this session.
                </p>
                <button
                    onClick={startQuiz}
                    className="w-full bg-app-bg text-app-fg py-3 rounded-lg font-bold hover:opacity-90 transition-opacity shadow-lg"
                >
                    Start Quiz
                </button>
            </div>
        </div>
    );
}

export default ResultsDisplay;
