import { contextBridge, ipcRenderer } from 'electron';

export interface ElectronAPI {
  getVersion: () => Promise<string>;
  openExternal: (url: string) => Promise<void>;
  openPath: (path: string) => Promise<string>;
  minimizeWindow: () => Promise<void>;
  maximizeWindow: () => Promise<void>;
  closeWindow: () => Promise<void>;
  isMaximized: () => Promise<boolean>;
  platform: string;
}

const api: ElectronAPI = {
  getVersion: () => ipcRenderer.invoke('app:version'),
  openExternal: (url: string) => ipcRenderer.invoke('app:openExternal', url),
  openPath: (filePath: string) => ipcRenderer.invoke('app:openPath', filePath),
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),
  platform: process.platform,
};

contextBridge.exposeInMainWorld('electronAPI', api);

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
