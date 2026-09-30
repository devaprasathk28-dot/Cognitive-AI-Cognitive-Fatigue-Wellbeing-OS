import { app, BrowserWindow, ipcMain, shell } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import * as http from 'http';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
const PYTHON_PORT = 8765;

function checkServerReady(timeoutMs = 10000): Promise<boolean> {
  const startTime = Date.now();
  return new Promise((resolve) => {
    const check = () => {
      const req = http.get(`http://127.0.0.1:${PYTHON_PORT}/api/status`, (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          retry();
        }
      });
      req.on('error', () => {
        retry();
      });
      req.end();
    };

    const retry = () => {
      if (Date.now() - startTime > timeoutMs) {
        resolve(false);
      } else {
        setTimeout(check, 500);
      }
    };

    check();
  });
}

function startPythonBackend() {
  const workspaceRoot = path.resolve(__dirname, '../../..');
  const bridgeScript = path.join(workspaceRoot, 'bridge_server.py');

  // Spawn bridge_server.py with python
  console.log(`[Electron Main] Launching bridge server: ${bridgeScript}`);
  try {
    pythonProcess = spawn('python', [bridgeScript], {
      cwd: workspaceRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
    });

    pythonProcess.stdout?.on('data', (data) => {
      console.log(`[Bridge Server] ${data.toString().trim()}`);
    });

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`[Bridge Server Error] ${data.toString().trim()}`);
    });

    pythonProcess.on('exit', (code) => {
      console.log(`[Bridge Server] Exited with code ${code}`);
      pythonProcess = null;
    });
  } catch (err) {
    console.error('[Electron Main] Failed to spawn python backend:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 1080,
    minHeight: 700,
    title: 'Cognitive AI — Fatigue & Wellbeing OS',
    backgroundColor: '#0A0D14',
    frame: true,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  // Open target URL
  const devUrl = 'http://localhost:5173';
  const prodPath = path.join(__dirname, '../../dist/index.html');

  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL(devUrl).catch(() => {
      // Fallback if Vite dev server not up
      mainWindow?.loadFile(prodPath);
    });
  } else {
    mainWindow.loadFile(prodPath);
  }

  // Handle external links securely
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Ensure single instance
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    // Check if server is already running, otherwise spawn it
    const isRunning = await checkServerReady(1000);
    if (!isRunning) {
      startPythonBackend();
    }

    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('will-quit', () => {
    if (pythonProcess) {
      console.log('[Electron Main] Terminating bridge server...');
      pythonProcess.kill();
      pythonProcess = null;
    }
  });
}

// IPC Handlers
ipcMain.handle('app:version', () => app.getVersion());
ipcMain.handle('app:openExternal', (_, url: string) => shell.openExternal(url));
