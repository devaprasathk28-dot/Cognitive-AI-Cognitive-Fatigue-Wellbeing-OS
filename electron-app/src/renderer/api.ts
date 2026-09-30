// Typed API client for Cognitive AI Bridge Server (http://127.0.0.1:8765)

export const BASE_URL = 'http://127.0.0.1:8765';

export interface SystemStatus {
  fatigue: number;
  focus_score: number;
  burnout: number;
  app: string;
  category: string;
  window_title: string;
  break_message: string;
  streak: number;
  timestamp: string;
  deep_work_sec: number;
  distraction_count: number;
  focus_mode: boolean;
  goal_focus_hours: number;
  goal_distraction_mins: number;
  goal_screen_time_hours: number;
}

export interface InsightItem {
  type: string;
  title: string;
  message: string;
  impact?: string;
  urgency?: string;
}

export interface AnalyticsCategory {
  category: string;
  duration_sec: number;
}

export interface AnalyticsApp {
  app: string;
  duration_sec: number;
  focus_score: number;
}

export interface AnalyticsDaily {
  date: string;
  minutes: number;
}

export interface AnalyticsData {
  days: number;
  categories: AnalyticsCategory[];
  apps: AnalyticsApp[];
  daily: AnalyticsDaily[];
}

export interface NotificationItem {
  id?: number;
  type: string;
  message: string;
  timestamp: string;
}

export interface ChatMessage {
  id?: number;
  user_prompt: string;
  ai_response: string;
  timestamp: string;
}

export interface AppSettings {
  focus_mode?: boolean;
  goal_focus_hours?: number;
  goal_distraction_mins?: number;
  goal_screen_time_hours?: number;
  autostart?: boolean;
  sound_effects?: boolean;
  theme?: string;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  getStatus: (): Promise<SystemStatus> => request<SystemStatus>('/api/status'),

  toggleFocusMode: (): Promise<{ focus_mode: boolean }> =>
    request<{ focus_mode: boolean }>('/api/focus/toggle', { method: 'POST' }),

  logFocusSession: (durationSec: number): Promise<{ success: boolean; duration_sec: number }> =>
    request<{ success: boolean; duration_sec: number }>('/api/focus/log', {
      method: 'POST',
      body: JSON.stringify({ duration_sec: durationSec }),
    }),

  completeBreak: (): Promise<{ success: boolean }> =>
    request<{ success: boolean }>('/api/break/complete', { method: 'POST' }),

  getInsights: (): Promise<{ insights: InsightItem[] }> =>
    request<{ insights: InsightItem[] }>('/api/insights'),

  getAnalytics: (days: number = 7): Promise<AnalyticsData> =>
    request<AnalyticsData>(`/api/analytics?days=${days}`),

  getNotifications: (): Promise<{ notifications: NotificationItem[] }> =>
    request<{ notifications: NotificationItem[] }>('/api/notifications'),

  clearNotifications: (): Promise<{ success: boolean }> =>
    request<{ success: boolean }>('/api/notifications/clear', { method: 'POST' }),

  getChatHistory: (): Promise<{ history: ChatMessage[] }> =>
    request<{ history: ChatMessage[] }>('/api/chat/history'),

  sendChatMessage: (prompt: string): Promise<{ reply: string }> =>
    request<{ reply: string }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),

  getSettings: (): Promise<AppSettings> => request<AppSettings>('/api/settings'),

  saveSettings: (settings: AppSettings): Promise<{ success: boolean; settings: AppSettings }> =>
    request<{ success: boolean; settings: AppSettings }>('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
};
