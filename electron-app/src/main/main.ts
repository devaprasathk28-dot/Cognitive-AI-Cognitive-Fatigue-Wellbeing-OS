import { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import * as http from 'http';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
let tray: Tray | null = null;
let isQuitting = false;
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

// Generate simple 16x16 RGBA brain/dot icon buffer for Tray
function createTrayIcon(): Electron.NativeImage {
  const size = 16;
  const buffer = Buffer.alloc(size * size * 4);
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const idx = (y * size + x) * 4;
      const dx = x - 7.5;
      const dy = y - 7.5;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist <= 6) {
        buffer[idx] = 126;     // R
        buffer[idx + 1] = 231; // G
        buffer[idx + 2] = 198; // B
        buffer[idx + 3] = 255; // A
      } else {
        buffer[idx + 3] = 0;   // Transparent
      }
    }
  }
  return nativeImage.createFromBuffer(buffer, { width: size, height: size });
}

function setupSystemTray() {
  try {
    const icon = createTrayIcon();
    tray = new Tray(icon);
    tray.setToolTip('Cognitive AI — Fatigue & Wellbeing OS');

    const contextMenu = Menu.buildFromTemplate([
      {
        label: '⚡ Open Cognitive Dashboard',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
          }
        },
      },
      {
        label: '🛡️ Toggle Focus Shield',
        click: () => {
          const req = http.request({
            hostname: '127.0.0.1',
            port: PYTHON_PORT,
            path: '/api/focus/toggle',
            method: 'POST',
          });
          req.on('error', () => {});
          req.end();
        },
      },
      {
        label: '🌬️ Take 4-7-8 Mindful Break',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
            mainWindow.webContents.send('action:open-breathing');
          }
        },
      },
      { type: 'separator' },
      {
        label: 'Exit Cognitive OS',
        click: () => {
          isQuitting = true;
          app.quit();
        },
      },
    ]);

    tray.setContextMenu(contextMenu);
    tray.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      }
    });
  } catch (err) {
    console.warn('[Electron Main] Tray initialization fallback:', err);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 1080,
    minHeight: 700,
    title: 'Cognitive AI — Fatigue & Wellbeing OS',
    backgroundColor: '#07090E',
    frame: false, // Frameless for modern custom titlebar
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  const devUrl = 'http://localhost:5173';
  const prodPath = path.join(__dirname, '../../dist/index.html');

  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL(devUrl).catch(() => {
      mainWindow?.loadFile(prodPath);
    });
  } else {
    mainWindow.loadFile(prodPath);
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Single Instance Lock
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    const isRunning = await checkServerReady(1000);
    if (!isRunning) {
      startPythonBackend();
    }

    createWindow();
    setupSystemTray();

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
ipcMain.handle('app:openPath', (_, filePath: string) => shell.openPath(filePath));

ipcMain.handle('window:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.handle('window:maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window:close', () => {
  mainWindow?.hide();
});

ipcMain.handle('window:isMaximized', () => {
  return mainWindow?.isMaximized() ?? false;
});
