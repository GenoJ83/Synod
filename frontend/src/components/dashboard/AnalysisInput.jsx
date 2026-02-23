import React from 'react';
import { Loader2, ChevronRight } from 'lucide-react';
import FileUploader from '../FileUploader';
import { cn } from '../../utils/cn'; // Assuming a utility or defining it inline

function AnalysisInput({ 
    activeTab, 
    setActiveTab, 
    text, 
    setText, 
    handleAnalyze, 
    handleFileUploadSuccess, 
    loading, 
    error,
    setError
}) {
    return (
        <div className="pro-card p-6 shadow-sm bg-app-card/30">
            <div className="flex gap-4 mb-6 border-b border-app-border pb-4">
                <button
                    onClick={() => setActiveTab('text')}
                    className={cn(
                        "text-sm font-bold uppercase tracking-widest px-4 py-2 rounded-md transition-all",
                        activeTab === 'text' ? "bg-app-fg text-app-bg shadow-lg" : "text-app-muted hover:text-app-fg"
                    )}
                >
                    Raw Text
                </button>
                <button
                    onClick={() => setActiveTab('file')}
                    className={cn(
                        "text-sm font-bold uppercase tracking-widest px-4 py-2 rounded-md transition-all",
                        activeTab === 'file' ? "bg-app-fg text-app-bg shadow-lg" : "text-app-muted hover:text-app-fg"
                    )}
                >
                    Documents
                </button>
            </div>

            {activeTab === 'text' ? (
                <div className="space-y-4 animate-fade-in">
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste lecture notes here..."
                        className="w-full h-80 pro-input resize-none font-mono text-sm leading-relaxed"
                    />
                    <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-app-muted uppercase tracking-widest">{text.length} chars</span>
                        <button
                            onClick={() => handleAnalyze()}
                            disabled={loading || !text}
                            className="bg-app-fg hover:opacity-90 text-app-bg px-6 py-3 rounded-lg font-bold text-sm transition-all flex items-center gap-2 disabled:opacity-50 shadow-md"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyze Content"}
                            {!loading && <ChevronRight className="w-4 h-4" />}
                        </button>
                    </div>
                </div>
            ) : (
                <div className="animate-fade-in">
                    <FileUploader onUploadSuccess={handleFileUploadSuccess} onError={setError} />
                </div>
            )}

            {error && <div className="mt-4 p-3 bg-red-950/20 border border-red-900/50 rounded-lg text-red-500 text-xs font-medium">{error}</div>}
        </div>
    );
}

export default AnalysisInput;
