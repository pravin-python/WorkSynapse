import { app, BrowserWindow } from 'electron';
import path from 'path';
import { PythonShell } from 'python-shell';

let mainWindow: BrowserWindow | null = null;
let pyshell: PythonShell | null = null;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, '../preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });

    // In production, load the built web app. For dev, we might load localhost:5173 if running parallel.
    // For this standalone desktop scaffold, we'll assume we point to a local file or dev server.
    // mainWindow.loadURL('http://localhost:5173'); 
    mainWindow.loadURL('https://worksynapse.local'); // Placeholder

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startWorkTracking() {
    // Spawn Python script
    const scriptPath = path.join(__dirname, '../../src/work-detection/activity_detector.py');

    // pyshell = new PythonShell(scriptPath, { mode: 'text' });

    // pyshell.on('message', function (message) {
    //   console.log('Activity update:', message);
    //   // Send to renderer or backend
    // });
}

app.on('ready', () => {
    createWindow();
    startWorkTracking();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
