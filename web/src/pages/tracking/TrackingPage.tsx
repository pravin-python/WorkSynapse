/**
 * WorkSynapse Time Tracking Page
 * ==============================
 * Track work hours with timer and reports.
 */
import React, { useState, useEffect } from 'react';
import { Timer, Play, Pause, Square, Clock, Calendar, BarChart3, Plus } from 'lucide-react';
import './Tracking.css';

interface TimeEntry {
    id: number;
    description: string;
    project: string;
    duration: number; // in seconds
    date: string;
}

export function TrackingPage() {
    const [isRunning, setIsRunning] = useState(false);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [currentTask, setCurrentTask] = useState('');
    const [entries, setEntries] = useState<TimeEntry[]>([
        { id: 1, description: 'API Development', project: 'WorkSynapse v2.0', duration: 7200, date: '2024-02-10' },
        { id: 2, description: 'Code Review', project: 'WorkSynapse v2.0', duration: 3600, date: '2024-02-10' },
        { id: 3, description: 'Meeting - Sprint Planning', project: 'General', duration: 5400, date: '2024-02-09' },
        { id: 4, description: 'Bug Fixes', project: 'Mobile App', duration: 4800, date: '2024-02-09' },
    ]);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (isRunning) {
            interval = setInterval(() => {
                setElapsedTime(prev => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [isRunning]);

    const formatTime = (seconds: number) => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const formatDuration = (seconds: number) => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return `${h}h ${m}m`;
    };

    const handleStart = () => setIsRunning(true);
    const handlePause = () => setIsRunning(false);
    const handleStop = () => {
        if (elapsedTime > 0) {
            setEntries([
                { id: Date.now(), description: currentTask || 'Untitled', project: 'General', duration: elapsedTime, date: new Date().toISOString().split('T')[0] },
                ...entries,
            ]);
        }
        setIsRunning(false);
        setElapsedTime(0);
        setCurrentTask('');
    };

    const todayTotal = entries
        .filter(e => e.date === new Date().toISOString().split('T')[0])
        .reduce((sum, e) => sum + e.duration, 0);

    return (
        <div className="tracking-page">
            <header className="page-header">
                <div className="header-content">
                    <h1><Timer size={28} />Time Tracking</h1>
                    <p>Track your work and stay productive</p>
                </div>
            </header>

            {/* Timer Section */}
            <div className="timer-section">
                <div className="timer-card">
                    <input
                        type="text"
                        className="task-input"
                        placeholder="What are you working on?"
                        value={currentTask}
                        onChange={(e) => setCurrentTask(e.target.value)}
                    />
                    <div className="timer-display">
                        <span className={`time ${isRunning ? 'running' : ''}`}>
                            {formatTime(elapsedTime)}
                        </span>
                    </div>
                    <div className="timer-controls">
                        {!isRunning ? (
                            <button className="btn btn-primary btn-lg" onClick={handleStart}>
                                <Play size={20} />
                                Start
                            </button>
                        ) : (
                            <>
                                <button className="btn btn-secondary" onClick={handlePause}>
                                    <Pause size={20} />
                                    Pause
                                </button>
                                <button className="btn btn-error" onClick={handleStop}>
                                    <Square size={20} />
                                    Stop
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <div className="stats-cards">
                    <div className="stat-mini">
                        <Clock size={20} />
                        <div>
                            <span className="stat-value">{formatDuration(todayTotal + elapsedTime)}</span>
                            <span className="stat-label">Today</span>
                        </div>
                    </div>
                    <div className="stat-mini">
                        <Calendar size={20} />
                        <div>
                            <span className="stat-value">38h 45m</span>
                            <span className="stat-label">This Week</span>
                        </div>
                    </div>
                    <div className="stat-mini">
                        <BarChart3 size={20} />
                        <div>
                            <span className="stat-value">156h</span>
                            <span className="stat-label">This Month</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Time Entries */}
            <div className="entries-section">
                <h2>Recent Entries</h2>
                <div className="entries-list">
                    {entries.map((entry) => (
                        <div key={entry.id} className="entry-item">
                            <div className="entry-info">
                                <span className="entry-description">{entry.description}</span>
                                <span className="entry-project">{entry.project}</span>
                            </div>
                            <div className="entry-meta">
                                <span className="entry-date">{entry.date}</span>
                                <span className="entry-duration">{formatDuration(entry.duration)}</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default TrackingPage;
