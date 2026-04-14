import React from 'react';
import { CheckCircle2, Brain, BookOpen, Lightbulb } from 'lucide-react';

/** Renders **markdown bold** in summary text (no full markdown engine). */
function SummaryInlineText({ text }) {
    const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
    return (
        <>
            {parts.map((part, i) => {
                const m = part.match(/^\*\*([^*]+)\*\*$/);
                if (m) {
                    return (
                        <strong key={i} className="font-semibold text-app-fg">
                            {m[1]}
                        </strong>
                    );
                }
                return <React.Fragment key={i}>{part}</React.Fragment>;
            })}
        </>
    );
}

function ResultsDisplay({ result, startQuiz }) {
    if (!result) return null;

    const totalQuestions = (result.quiz?.mcqs?.length || 0) +
        (result.quiz?.fill_in_the_blanks?.length || 0) +
        (result.quiz?.true_false?.length || 0) +
        (result.quiz?.comprehension?.length || 0);

    return (
        <div className="w-full xl:w-2/3 max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
            {/* Executive Summary Section */}
            <div className="pro-card p-8 shadow-sm">
                <div className="flex items-center gap-3 mb-6 text-emerald-500">
                    <CheckCircle2 className="w-6 h-6" />
                    <h3 className="text-sm font-bold uppercase tracking-widest">Comprehensive Summary</h3>
                </div>
                <div className="space-y-4">
                    {result.summary.split('\n\n').map((paragraph, index) => (
                        <p key={index} className="text-app-fg text-lg leading-relaxed font-medium">
                            <SummaryInlineText text={paragraph} />
                        </p>
                    ))}
                </div>

                {result.metrics?.compression_ratio && (
                    <div className="mt-8 pt-6 border-t border-app-border/30 grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="flex flex-col gap-2">
                            <span className="text-[10px] font-bold text-app-muted uppercase tracking-widest">Efficiency</span>
                            <div className="flex items-center gap-3">
                                <div className="flex-1 h-1.5 bg-app-card rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-emerald-500 rounded-full"
                                        style={{ width: `${Math.min(100, result.metrics.compression_ratio * 100)}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold text-emerald-500">{(result.metrics.compression_ratio * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                        {result.metrics?.coverage_score !== undefined && (
                            <div className="flex flex-col gap-2">
                                <span className="text-[10px] font-bold text-app-muted uppercase tracking-widest">Precision Range</span>
                                <div className="flex items-center gap-3">
                                    <div className="flex-1 h-1.5 bg-app-card rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 rounded-full"
                                            style={{ width: `${Math.min(100, result.metrics.coverage_score * 100)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-bold text-blue-500">{(result.metrics.coverage_score * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Key Takeaways Section */}
            {result.takeaways && result.takeaways.length > 0 && (
                <div className="pro-card p-8 shadow-sm">
                    <div className="flex items-center gap-3 mb-6 text-blue-500">
                        <Lightbulb className="w-6 h-6" />
                        <h3 className="text-sm font-bold uppercase tracking-widest">Key Takeaways</h3>
                    </div>
                    <ul className="space-y-4">
                        {result.takeaways.map((takeaway, idx) => (
                            <li key={idx} className="flex gap-4 group items-start">
                                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center text-xs font-bold mt-0.5">
                                    {idx + 1}
                                </span>
                                <p className="text-app-fg text-base font-medium leading-relaxed group-hover:text-blue-500 transition-colors">
                                    {takeaway}
                                </p>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Fundamental Concepts Section */}
            {result.explanations?.concepts && result.explanations.concepts.length > 0 && (
                <div className="pro-card p-8 shadow-sm">
                    <div className="flex items-center gap-3 mb-6 text-purple-500">
                        <BookOpen className="w-6 h-6" />
                        <h3 className="text-sm font-bold uppercase tracking-widest">Fundamental Concepts</h3>
                    </div>
                    {result.explanations.global && (
                        <p className="text-app-muted italic text-sm mb-6 pb-6 border-b border-app-border/30">
                            {result.explanations.global}
                        </p>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {result.explanations.concepts.map((conceptObj, idx) => (
                            <div key={idx} className="bg-app-bg/50 border border-app-border/50 rounded-lg p-5 hover:border-purple-500/30 transition-colors">
                                <h4 className="text-purple-400 font-bold capitalize mb-2">{conceptObj.term}</h4>
                                <p className="text-app-fg text-sm leading-relaxed mb-2"><span className="font-bold text-app-muted">Definition:</span> {conceptObj.definition}</p>
                                {conceptObj.context && (
                                    <p className="text-app-muted text-sm leading-relaxed italic border-l-2 border-purple-500/20 pl-3"><span className="font-bold not-italic">Context:</span> {conceptObj.context}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Knowledge Check CTA */}
            <div className="relative overflow-hidden bg-gradient-to-br from-app-fg to-zinc-400 text-app-bg rounded-2xl p-10 flex flex-col items-center justify-center text-center shadow-xl group">
                {/* Decorative background elements */}
                <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-white/20 rounded-full blur-3xl group-hover:bg-white/30 transition-all duration-500"></div>
                <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-32 h-32 bg-white/20 rounded-full blur-2xl group-hover:bg-white/30 transition-all duration-500"></div>

                <Brain className="w-12 h-12 mb-4 opacity-90 drop-shadow-md z-10" />
                <h3 className="text-2xl font-black mb-3 z-10 tracking-tight">Ready to test your knowledge?</h3>
                <p className="text-app-bg/80 text-base mb-8 font-semibold max-w-sm z-10">
                    We've generated {totalQuestions} interactive questions based on the concepts extracted from your document.
                </p>
                <button
                    onClick={startQuiz}
                    className="z-10 bg-app-bg text-app-fg px-10 py-4 rounded-xl font-bold text-lg hover:bg-zinc-800 transition-all hover:scale-105 active:scale-95 shadow-lg border border-app-bg"
                >
                    Start Knowledge Check
                </button>
            </div>
        </div>
    );
}

export default ResultsDisplay;
