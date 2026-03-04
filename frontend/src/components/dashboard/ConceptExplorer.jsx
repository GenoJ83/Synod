import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';

function ConceptExplorer({
    result,
    selectedConcept,
    setSelectedConcept,
    viewedConcepts,
    setViewedConcepts,
    setShowQuiz,
    quizRef
}) {
    if (!result?.concepts) return null;

    return (
        <div className="pro-card p-6">
            <div className="flex items-center gap-3 mb-4 text-app-muted">
                <BookOpen className="w-4 h-4" />
                <h3 className="text-xs font-bold uppercase tracking-widest">Foundational Concepts</h3>
                <span className="ml-auto text-[10px] text-blue-400">
                    {viewedConcepts.length}/{result.concepts.length} explored
                </span>
            </div>
            <div className="flex flex-wrap gap-2">
                {result.concepts.map((concept, i) => {
                    const detail = result.concept_details?.find(d => d.term === concept);
                    const relevance = detail?.relevance || 0;
                    return (
                        <button
                            key={i}
                            onClick={() => {
                                setSelectedConcept(concept);
                                if (!viewedConcepts.includes(concept)) {
                                    setViewedConcepts([...viewedConcepts, concept]);
                                }
                            }}
                            className={`px-3 py-1 bg-app-card border rounded-md text-[11px] font-bold uppercase transition-all cursor-pointer flex items-center gap-2 ${selectedConcept === concept
                                ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                                : viewedConcepts.includes(concept)
                                    ? 'border-green-500/30 text-green-400/70'
                                    : 'border-app-border text-app-muted hover:bg-blue-500/20 hover:border-blue-500/50 hover:text-blue-400'
                                }`}
                        >
                            {concept}
                            {relevance > 0 && (
                                <span className={`text-[8px] px-1 rounded ${relevance > 0.7 ? 'bg-emerald-500/20 text-emerald-500' : 'bg-blue-500/20 text-blue-500'}`}>
                                    {(relevance * 100).toFixed(0)}%
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Interactive Concept Explanation */}
            {selectedConcept && result.explanations?.concepts && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-4 p-5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-xl"
                >
                    <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                <BookOpen className="w-4 h-4 text-blue-400" />
                            </div>
                            <div>
                                <h4 className="text-base font-bold text-blue-400">{selectedConcept}</h4>
                                {result.concept_details?.find(d => d.term === selectedConcept) && (
                                    <p className="text-[10px] text-app-muted font-bold uppercase">
                                        Semantic Confidence: {(result.concept_details.find(d => d.term === selectedConcept).relevance * 100).toFixed(1)}%
                                    </p>
                                )}
                            </div>
                        </div>
                        <button
                            onClick={() => setSelectedConcept(null)}
                            className="text-app-muted hover:text-app-fg p-1 hover:bg-app-card rounded"
                        >
                            ×
                        </button>
                    </div>

                    <p className="text-sm text-app-fg leading-relaxed mb-4">
                        <span className="font-bold">Definition:</span> {result.explanations.concepts.find(c => c.term === selectedConcept)?.definition || result.explanations.global}
                    </p>
                    {result.explanations.concepts.find(c => c.term === selectedConcept)?.context && (
                        <p className="text-sm text-app-fg leading-relaxed mb-4 italic border-l-2 border-blue-500/30 pl-3">
                            <span className="font-bold not-italic">In Context:</span> {result.explanations.concepts.find(c => c.term === selectedConcept)?.context}
                        </p>
                    )}

                    {/* Related Concepts */}
                    <div className="pt-3 border-t border-blue-500/20">
                        <p className="text-[10px] font-bold text-app-muted uppercase tracking-wider mb-2">Related Concepts</p>
                        <div className="flex flex-wrap gap-1">
                            {result.concepts.filter(c => c !== selectedConcept).slice(0, 4).map((related, i) => (
                                <button
                                    key={i}
                                    onClick={() => setSelectedConcept(related)}
                                    className="px-2 py-1 bg-app-card/50 border border-app-border/50 rounded text-[10px] text-app-muted hover:text-blue-400 hover:border-blue-500/50 transition-all"
                                >
                                    {related}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex gap-2 mt-4">
                        <button
                            onClick={() => {
                                setShowQuiz(true);
                                setTimeout(() => quizRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
                            }}
                            className="flex-1 py-2 bg-blue-500 text-white text-xs font-bold rounded-lg hover:bg-blue-600 transition-colors"
                        >
                            Test Your Knowledge
                        </button>
                    </div>
                </motion.div>
            )}
        </div>
    );
}

export default ConceptExplorer;
