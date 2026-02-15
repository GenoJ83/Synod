import React, { useState, useRef } from 'react';
import axios from 'axios';
import { FileText, BookOpen, Brain, CheckCircle2, ChevronRight, Loader2, History as HistoryIcon, Upload } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import QuizSection from '../components/QuizSection';
import FileUploader from '../components/FileUploader';
import { useNavigate } from 'react-router-dom';

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

const API_BASE_URL = 'http://localhost:8000';

function Dashboard() {
                )
}
            </main >
        </div >
    );
}

export default Dashboard;
