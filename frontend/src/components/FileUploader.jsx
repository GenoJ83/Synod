import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const FileUploader = ({ onUploadSuccess }) => {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle'); // idle, uploading, success, error
    const [message, setMessage] = useState('');

    const onDrop = useCallback(acceptedFiles => {
        const selectedFile = acceptedFiles[0];
        if (selectedFile) {
            setFile(selectedFile);
            setStatus('idle');
            setMessage('');
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt']
        },
        multiple: false
    });

    const handleUpload = async () => {
        if (!file) return;

        setStatus('uploading');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/analyze-file', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Failed to upload file');

            const data = await response.json();
            setStatus('success');
            setMessage('File analyzed successfully!');
            setTimeout(() => {
                onUploadSuccess(data);
            }, 1000);
        } catch (err) {
            console.error(err);
            setStatus('error');
            setMessage('Failed to process file. Please try again.');
        }
    };

    const removeFile = (e) => {
        e.stopPropagation();
        setFile(null);
        setStatus('idle');
    };

    return (
        <div className="w-full">
            <div
                {...getRootProps()}
                className={`relative border-2 border-dashed rounded-3xl p-12 transition-all cursor-pointer group flex flex-col items-center justify-center text-center
                ${isDragActive ? 'border-blue-500 bg-blue-500/5' : 'border-slate-800 hover:border-slate-700 bg-slate-900/30'}`}
            >
                <input {...getInputProps()} />

                <AnimatePresence mode='wait'>
                    {!file ? (
                        <motion.div
                            key="empty"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="flex flex-col items-center"
                        >
                            <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-500 mb-6 group-hover:scale-110 transition-transform">
                                <Upload className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Drag & Drop Lecture Materials</h3>
                            <p className="text-slate-500 text-sm max-w-xs">
                                Support for PDF, PPTX, and TXT files.<br />MAX size: 10MB
                            </p>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="file"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="w-full max-w-md bg-slate-950 border border-slate-800 p-6 rounded-2xl relative"
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                                    <File className="w-6 h-6" />
                                </div>
                                <div className="flex-1 text-left overflow-hidden">
                                    <h4 className="font-bold text-white truncate">{file.name}</h4>
                                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button
                                    onClick={removeFile}
                                    className="p-2 text-slate-500 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="mt-6">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleUpload();
                                    }}
                                    disabled={status === 'uploading'}
                                    className={`w-full py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2
                                    ${status === 'uploading' ? 'bg-slate-800 text-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20'}`}
                                >
                                    {status === 'uploading' ? (
                                        <>
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Processing...
                                        </>
                                    ) : (
                                        'Start Analysis'
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <AnimatePresence>
                {status !== 'idle' && status !== 'uploading' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={`mt-4 p-4 rounded-xl border flex items-center gap-3 ${status === 'success' ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' : 'bg-red-500/10 border-red-500/50 text-red-400'}`}
                    >
                        {status === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                        <span className="font-bold text-sm tracking-tight">{message}</span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default FileUploader;
