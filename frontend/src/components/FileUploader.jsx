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
        setUploading(true);
        // Simulate upload
        await new Promise(resolve => setTimeout(resolve, 2000));
        setUploading(false);
        onUploadSuccess("Successfully synthesized knowledge from uploaded materials.");
        setFiles([]);
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
                        {status === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                        <span className="font-bold text-xs uppercase tracking-widest">{message}</span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default FileUploader;
