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
                className={`relative border border-zinc-800 rounded-xl p-12 transition-all cursor-pointer group flex flex-col items-center justify-center text-center bg-zinc-950/50
                ${isDragActive ? 'border-zinc-500 bg-zinc-900/50' : 'hover:border-zinc-700 hover:bg-zinc-900/30'}`}
            >
                <input {...getInputProps()} />

                <AnimatePresence mode='wait'>
                    {!file ? (
                        <div className="flex flex-col items-center">
                            <div className="w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center justify-center text-zinc-500 mb-6 group-hover:bg-zinc-100 group-hover:text-zinc-950 transition-all">
                                <Upload className="w-6 h-6" />
                            </div>
                            <h3 className="text-lg font-bold text-zinc-200 mb-2">Upload Lecture Materials</h3>
                            <p className="text-zinc-500 text-sm max-w-xs">
                                PDF, PPTX, or TXT (Max 10MB)
                            </p>
                        </div>
                    ) : (
                        <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 p-6 rounded-xl relative shadow-xl">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-400">
                                    <File className="w-6 h-6" />
                                </div>
                                <div className="flex-1 text-left overflow-hidden">
                                    <h4 className="font-bold text-zinc-200 truncate">{file.name}</h4>
                                    <p className="text-[10px] font-bold text-zinc-500 uppercase">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                <button
                                    onClick={removeFile}
                                    className="p-2 text-zinc-600 hover:text-red-500 hover:bg-zinc-950 rounded-lg transition-all"
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
                                    className={`w-full py-3 rounded-lg font-bold text-sm transition-all flex items-center justify-center gap-2
                                    ${status === 'uploading' ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' : 'bg-zinc-100 hover:bg-white text-zinc-950 shadow-sm'}`}
                                >
                                    {status === 'uploading' ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : (
                                        'Process Document'
                                    )}
                                </button>
                            </div>
                        </div>
                    )}
                </AnimatePresence>
            </div>

            <AnimatePresence>
                {status !== 'idle' && status !== 'uploading' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={`mt-4 p-4 rounded-xl border flex items-center gap-3 shadow-sm ${status === 'success' ? 'bg-emerald-950/20 border-emerald-900/50 text-emerald-500' : 'bg-red-950/20 border-red-900/50 text-red-500'}`}
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
