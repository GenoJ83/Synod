import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2, FileUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const FileUploader = ({ onUploadSuccess }) => {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);

    const onDrop = useCallback((acceptedFiles) => {
        setFiles(prev => [...prev, ...acceptedFiles.map(file => ({
            file,
            id: Math.random().toString(36).substr(2, 9),
            status: 'queued'
        }))]);
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt']
        }
    });

    const removeFile = (id) => {
        setFiles(prev => prev.filter(f => f.id !== id));
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', files[0].file);

            const response = await fetch('http://localhost:8000/analyze-file', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            onUploadSuccess(data);
            setFiles([]);
        } catch (error) {
            console.error('Upload error:', error);
            // You might want to add an error state/toast here
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div
                {...getRootProps()}
                className={`
                    border-2 border-dashed rounded-[2rem] p-12 transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-4
                    ${isDragActive ? 'border-blue-500 bg-blue-500/5' : 'border-app-border hover:border-app-muted bg-app-card/30'}
                `}
            >
                <input {...getInputProps()} />
                <div className={`w-20 h-20 rounded-[2rem] flex items-center justify-center transition-transform duration-500 ${isDragActive ? 'scale-110 bg-blue-500 text-white' : 'bg-app-card border border-app-border text-app-muted'}`}>
                    <FileUp className="w-10 h-10" />
                </div>
                <div>
                    <p className="text-lg font-bold">Drop your lecture materials here</p>
                    <p className="text-app-muted text-sm mt-1">PDF, PPTX, or TXT documents (Max 50MB)</p>
                </div>
                <button className={`mt-4 px-6 py-2 rounded-xl text-sm font-bold transition-all ${isDragActive ? 'bg-blue-600 text-white' : 'bg-app-fg text-app-bg hover:opacity-90'}`}>
                    Browse Files
                </button>
            </div>

            <AnimatePresence>
                {files.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="space-y-3"
                    >
                        {files.map(({ file, id, status }) => (
                            <div key={id} className="flex items-center justify-between p-4 bg-app-card border border-app-border rounded-xl">
                                <div className="flex items-center gap-3 flex-1">
                                    <FileText className="w-5 h-5 text-blue-500" />
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm truncate">{file.name}</p>
                                        <p className="text-xs text-app-muted">{(file.size / 1024).toFixed(1)} KB</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeFile(id)}
                                    className="p-2 hover:bg-app-bg rounded-lg transition-colors text-app-muted hover:text-red-500"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ))}

                        <button
                            onClick={handleUpload}
                            disabled={uploading}
                            className="w-full bg-app-fg text-app-bg py-3 rounded-xl font-bold text-sm hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Upload className="w-4 h-4" />
                                    Upload & Synthesize
                                </>
                            )}
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default FileUploader;
