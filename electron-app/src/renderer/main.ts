import confetti from 'canvas-confetti';
import { api, SystemStatus, InsightItem, AnalyticsData, NotificationItem, ChatMessage, AppSettings } from './api';
import { soundEngine } from './audio';

// State Management
let currentPage = 'dashboard';
let systemStatus: SystemStatus | null = null;
let pollInterval: number | null = null;

// Sprint Timer State
let sprintTimerInterval: number | null = null;
let sprintTotalSeconds = 25 * 60;
let sprintRemainingSeconds = 25 * 60;
let isSprintRunning = false;

// 4-7-8 Breathing State
let breathingInterval: number | null = null;
let breathingCycle = 1;
const TOTAL_BREATHING_CYCLES = 4;
let breathingPhase: 'inhale' | 'hold' | 'exhale' | 'ready' = 'ready';
let breathingSecondsLeft = 4;

// Audio Chime Helper
function playTone(freq: number, duration: number, type: OscillatorType = 'sine') {
  try {
    const ctx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch {
    // Ignore audio context autoplay restrictions
  }
}

// Helpers
function formatSeconds(totalSec: number): string {
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatHoursAndMins(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function getFocusColor(score: number): string {
  if (score >= 75) return '#10B981'; // Emerald
  if (score >= 45) return '#F59E0B'; // Amber
  return '#F43F5E'; // Coral
}

// ==========================================================================
// INITIALIZATION & ROUTING
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupCommandPalette();
  setupBreathingModal();
  setupTopBarActions();

  // Initial Fetch & Start Polling
  fetchLatestStatus();
  pollInterval = window.setInterval(fetchLatestStatus, 3000);

  // Render initial page
  renderCurrentPage();
});

function setupNavigation() {
  const navButtons = document.querySelectorAll<HTMLButtonElement>('.sidebar-nav .nav-item');
  navButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const page = btn.dataset.page;
      if (page) navigateTo(page);
    });
  });
}

export function navigateTo(page: string) {
  currentPage = page;
  document.querySelectorAll<HTMLButtonElement>('.sidebar-nav .nav-item').forEach((b) => {
    b.classList.toggle('active', b.dataset.page === page);
  });
  renderCurrentPage();
}

async function fetchLatestStatus() {
  try {
    systemStatus = await api.getStatus();
    updateTopBar(systemStatus);
    updateEngineDot(true);

    // If active page is dashboard or streaks, update live parts
    if (currentPage === 'dashboard') {
      updateDashboardLiveMetrics(systemStatus);
    }
  } catch (err) {
    console.warn('[Status Fetch Warning]', err);
    updateEngineDot(false);
  }
}

function updateEngineDot(connected: boolean) {
  const dot = document.getElementById('engine-status-dot');
  const text = document.getElementById('engine-status-text');
  const sub = document.getElementById('engine-status-sub');
  if (dot && text && sub) {
    dot.className = `engine-dot ${connected ? 'connected' : 'disconnected'}`;
    text.textContent = connected ? 'Backend Connected' : 'Connecting Engine...';
    sub.textContent = connected ? 'Live Tracking Active' : 'Port 8765';
  }
}

function updateTopBar(status: SystemStatus) {
  const appLabel = document.getElementById('topbar-app-name');
  const appCat = document.getElementById('topbar-app-cat');
  const shieldBtn = document.getElementById('focus-shield-toggle');
  const shieldLabel = document.getElementById('focus-shield-label');

  if (appLabel) appLabel.textContent = status.app || 'Desktop';
  if (appCat) appCat.textContent = status.category || 'General';

  if (shieldBtn && shieldLabel) {
    shieldBtn.classList.toggle('active', !!status.focus_mode);
    shieldLabel.textContent = status.focus_mode ? 'Focus Shield: ACTIVE' : 'Focus Shield: OFF';
  }
}

function setupTopBarActions() {
  const shieldBtn = document.getElementById('focus-shield-toggle');
  shieldBtn?.addEventListener('click', async () => {
    try {
      const res = await api.toggleFocusMode();
      if (systemStatus) systemStatus.focus_mode = res.focus_mode;
      updateTopBar(systemStatus!);
      playTone(res.focus_mode ? 520 : 380, 0.2);
    } catch (e) {
      console.error(e);
    }
  });

  const breatheBtn = document.getElementById('breathe-trigger-btn');
  breatheBtn?.addEventListener('click', () => {
    openBreathingModal();
  });
}

// ==========================================================================
// PAGE RENDERERS
// ==========================================================================
function renderCurrentPage() {
  const container = document.getElementById('content-area');
  if (!container) return;

  switch (currentPage) {
    case 'dashboard':
      renderDashboard(container);
      break;
    case 'focus':
      renderFocusSprint(container);
      break;
    case 'insights':
      renderInsights(container);
      break;
    case 'analytics':
      renderAnalytics(container);
      break;
    case 'coach':
      renderAiCoach(container);
      break;
    case 'streaks':
      renderStreaks(container);
      break;
    case 'notifications':
      renderNotifications(container);
      break;
    case 'settings':
      renderSettings(container);
      break;
    default:
      renderDashboard(container);
  }
}

// --------------------------------------------------------------------------
// 1. DASHBOARD PAGE
// --------------------------------------------------------------------------
function renderDashboard(container: HTMLElement) {
  const status = systemStatus || {
    fatigue: 0.0,
    focus_score: 100,
    burnout: 0.0,
    app: 'Initializing',
    category: 'General',
    window_title: '',
    break_message: 'Cognitive engine analyzing activity stream.',
    streak: 1,
    deep_work_sec: 0,
    distraction_count: 0,
    focus_mode: false,
    timestamp: '',
    goal_focus_hours: 5,
    goal_distraction_mins: 60,
    goal_screen_time_hours: 8,
  };

  const focusScore = status.focus_score;
  const strokeOffset = 565 - (565 * focusScore) / 100;
  const focusColor = getFocusColor(focusScore);

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Executive Cognitive Dashboard</h1>
        <p class="page-subtitle">Real-time mental fatigue modeling, stamina metrics, and neural recovery cues.</p>
      </div>
      <div style="display:flex; gap:10px;">
        <button class="btn btn-primary" id="dash-start-sprint-btn">
          <span>🎯 Start 25m Sprint</span>
        </button>
      </div>
    </div>

    <!-- 4 Key Metric Tiles -->
    <div class="grid-cols-4">
      <div class="glass-card metric-tile">
        <div class="tile-top">
          <span class="tile-label">Deep Work Today</span>
          <span class="tile-icon">⏱️</span>
        </div>
        <div class="tile-value-row">
          <span class="tile-value" id="dash-deep-work-val">${formatHoursAndMins(status.deep_work_sec)}</span>
        </div>
        <span class="tile-sub">Target: ${status.goal_focus_hours}h focus goal</span>
      </div>

      <div class="glass-card metric-tile">
        <div class="tile-top">
          <span class="tile-label">Distractions & Switches</span>
          <span class="tile-icon">⚡</span>
        </div>
        <div class="tile-value-row">
          <span class="tile-value ${status.distraction_count > 15 ? 'text-coral' : 'text-emerald'}" id="dash-distractions-val">${status.distraction_count}</span>
          <span class="tile-unit">switches</span>
        </div>
        <span class="tile-sub">${status.distraction_count <= 8 ? 'Exceptional focus sustained' : 'Consider activating Shield'}</span>
      </div>

      <div class="glass-card metric-tile">
        <div class="tile-top">
          <span class="tile-label">Burnout Probability</span>
          <span class="tile-icon">🛡️</span>
        </div>
        <div class="tile-value-row">
          <span class="tile-value ${status.burnout > 0.4 ? 'text-coral' : 'text-teal'}" id="dash-burnout-val">${Math.round(status.burnout * 100)}%</span>
        </div>
        <span class="tile-sub">Cumulative cognitive strain index</span>
      </div>

      <div class="glass-card metric-tile">
        <div class="tile-top">
          <span class="tile-label">Active Habit Streak</span>
          <span class="tile-icon">🔥</span>
        </div>
        <div class="tile-value-row">
          <span class="tile-value text-amber" id="dash-streak-val">${status.streak}</span>
          <span class="tile-unit">days</span>
        </div>
        <span class="tile-sub">Consecutive deep work days</span>
      </div>
    </div>

    <!-- Main Center Grid: Circular Stamina Ring & Current Neural State -->
    <div class="grid-cols-2">
      <!-- Circular Stamina Gauge -->
      <div class="glass-card gauge-container">
        <svg class="gauge-svg" viewBox="0 0 200 200">
          <circle class="gauge-bg" cx="100" cy="100" r="90" />
          <circle class="gauge-progress" id="gauge-circle" cx="100" cy="100" r="90"
            style="stroke-dashoffset: ${strokeOffset}; stroke: ${focusColor};" />
        </svg>
        <div class="gauge-content">
          <span class="gauge-score" id="dash-gauge-score" style="color: ${focusColor};">${focusScore}</span>
          <span class="gauge-title">Focus Stamina</span>
          <span class="gauge-status-badge" id="dash-gauge-badge" style="background: ${focusColor}20; color: ${focusColor};">
            ${focusScore >= 75 ? 'OPTIMAL PEAK' : focusScore >= 45 ? 'MODERATE FATIGUE' : 'DEPLETED / BREAK NEEDED'}
          </span>
        </div>
      </div>

      <!-- Neural State & Recommended Interventions -->
      <div class="glass-card" style="display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div class="tile-top" style="margin-bottom:12px;">
            <span class="tile-label">Cognitive State & Interventions</span>
            <span class="pill-category">Live Model</span>
          </div>
          <h3 style="font-size:18px; font-weight:700; margin-bottom:8px; line-height:1.4;" id="dash-break-message">
            "${status.break_message}"
          </h3>
          <p style="font-size:13px; color:var(--text-secondary); line-height:1.6; margin-bottom:16px;">
            Your mental fatigue coefficient is currently <strong>${status.fatigue.toFixed(2)}</strong>.
            Neural recovery algorithms recommend a targeted 4-7-8 breathing interval or switching to a lower-friction task.
          </p>
        </div>

        <div style="display:flex; gap:12px;">
          <button class="btn btn-secondary" id="dash-breathe-btn" style="flex:1;">
            <span>🌬️ Mindful Reset</span>
          </button>
          <button class="btn btn-primary" id="dash-coach-btn" style="flex:1;">
            <span>🤖 Consult AI Coach</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Active Application Activity Stream -->
    <div class="glass-card">
      <div class="tile-top">
        <span class="tile-label">Foreground Tracking Stream</span>
        <span class="tile-sub">Real-time foreground OS window</span>
      </div>
      <div class="activity-feed-list">
        <div class="activity-item">
          <div>
            <span class="activity-app-name" id="dash-current-app">${status.app}</span>
            <span class="activity-category-tag" id="dash-current-cat">${status.category}</span>
          </div>
          <span class="activity-duration" id="dash-current-title">${status.window_title ? status.window_title.substring(0, 45) + '...' : 'Active Foreground Session'}</span>
        </div>
      </div>
    </div>
  `;

  // Attach Dashboard Event Listeners
  document.getElementById('dash-start-sprint-btn')?.addEventListener('click', () => navigateTo('focus'));
  document.getElementById('dash-breathe-btn')?.addEventListener('click', () => openBreathingModal());
  document.getElementById('dash-coach-btn')?.addEventListener('click', () => navigateTo('coach'));
}

function updateDashboardLiveMetrics(status: SystemStatus) {
  const deepWorkVal = document.getElementById('dash-deep-work-val');
  const distVal = document.getElementById('dash-distractions-val');
  const burnoutVal = document.getElementById('dash-burnout-val');
  const streakVal = document.getElementById('dash-streak-val');
  const gaugeScore = document.getElementById('dash-gauge-score');
  const gaugeCircle = document.getElementById('gauge-circle') as SVGPathElement | null;
  const gaugeBadge = document.getElementById('dash-gauge-badge');
  const breakMsg = document.getElementById('dash-break-message');
  const curApp = document.getElementById('dash-current-app');
  const curCat = document.getElementById('dash-current-cat');
  const curTitle = document.getElementById('dash-current-title');

  if (deepWorkVal) deepWorkVal.textContent = formatHoursAndMins(status.deep_work_sec);
  if (distVal) distVal.textContent = status.distraction_count.toString();
  if (burnoutVal) burnoutVal.textContent = `${Math.round(status.burnout * 100)}%`;
  if (streakVal) streakVal.textContent = status.streak.toString();

  const score = status.focus_score;
  const color = getFocusColor(score);
  const strokeOffset = 565 - (565 * score) / 100;

  if (gaugeScore) {
    gaugeScore.textContent = score.toString();
    gaugeScore.style.color = color;
  }
  if (gaugeCircle) {
    gaugeCircle.style.strokeDashoffset = strokeOffset.toString();
    gaugeCircle.style.stroke = color;
  }
  if (gaugeBadge) {
    gaugeBadge.style.background = `${color}20`;
    gaugeBadge.style.color = color;
    gaugeBadge.textContent = score >= 75 ? 'OPTIMAL PEAK' : score >= 45 ? 'MODERATE FATIGUE' : 'DEPLETED / BREAK NEEDED';
  }

  if (breakMsg) breakMsg.textContent = `"${status.break_message}"`;
  if (curApp) curApp.textContent = status.app;
  if (curCat) curCat.textContent = status.category;
  if (curTitle && status.window_title) {
    curTitle.textContent = status.window_title.length > 50 ? status.window_title.substring(0, 48) + '...' : status.window_title;
  }
}

// --------------------------------------------------------------------------
// 2. FOCUS SPRINT & SOUNDSCAPES PAGE
// --------------------------------------------------------------------------
function renderFocusSprint(container: HTMLElement) {
  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Neural Focus Sprint & Soundscapes</h1>
        <p class="page-subtitle">Immersive deep work cycles backed by real-time binaural beats and acoustic dampening.</p>
      </div>
    </div>

    <!-- Timer Hero -->
    <div class="sprint-hero">
      <div class="sprint-mode-tabs">
        <button class="sprint-tab active" data-mins="25">25m Pomodoro</button>
        <button class="sprint-tab" data-mins="50">50m Deep Work</button>
        <button class="sprint-tab" data-mins="90">90m Flow State</button>
        <button class="sprint-tab" data-mins="5">5m Micro Break</button>
      </div>

      <div class="sprint-timer-display" id="sprint-timer-text">${formatSeconds(sprintRemainingSeconds)}</div>
      <p class="sprint-status-note" id="sprint-status-note">
        ${isSprintRunning ? 'Deep Focus Session In Progress — Distractions Shielded' : 'Select a focus duration and begin when ready.'}
      </p>

      <div class="sprint-controls">
        <button class="btn btn-primary" id="sprint-toggle-btn" style="min-width:140px; padding:12px 24px;">
          <span>${isSprintRunning ? '⏸️ Pause' : '▶️ Begin Sprint'}</span>
        </button>
        <button class="btn btn-secondary" id="sprint-reset-btn" style="padding:12px 20px;">
          <span>↺ Reset</span>
        </button>
      </div>
    </div>

    <!-- Ambient Soundscape Engine -->
    <div class="glass-card soundscape-card">
      <div class="tile-top">
        <div>
          <span class="tile-label">Ambient Audio Engine</span>
          <h3 style="font-size:16px; font-weight:700; margin-top:2px;">Acoustic Cognitive Soundscapes</h3>
        </div>
        <button class="btn btn-secondary btn-icon" id="soundscape-stop-all" title="Mute Soundscapes">
          <span>🔇 Mute</span>
        </button>
      </div>

      <!-- Alpha Waves (14Hz) -->
      <div class="soundscape-row">
        <div class="soundscape-info">
          <span class="soundscape-title">14Hz Alpha Binaural Drone</span>
          <span class="soundscape-desc">Stimulates parietal alpha rhythm associated with calm focus and memory consolidation.</span>
        </div>
        <div class="soundscape-actions">
          <div class="audio-visualizer ${soundEngine.isPlaying('alpha') ? 'playing' : ''}" id="vis-alpha">
            <span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span>
          </div>
          <input type="range" class="volume-slider" min="0" max="1" step="0.05" value="${soundEngine.getVolume()}" id="vol-alpha" />
          <button class="btn ${soundEngine.isPlaying('alpha') ? 'btn-danger' : 'btn-secondary'}" data-sound="alpha" id="btn-sound-alpha">
            <span>${soundEngine.isPlaying('alpha') ? 'Stop' : 'Play'}</span>
          </button>
        </div>
      </div>

      <!-- Brown Noise -->
      <div class="soundscape-row">
        <div class="soundscape-info">
          <span class="soundscape-title">Deep Brown Noise</span>
          <span class="soundscape-desc">Deep low-frequency acoustic mask that suppresses ambient conversation and startling noises.</span>
        </div>
        <div class="soundscape-actions">
          <div class="audio-visualizer ${soundEngine.isPlaying('brown') ? 'playing' : ''}" id="vis-brown">
            <span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span>
          </div>
          <input type="range" class="volume-slider" min="0" max="1" step="0.05" value="${soundEngine.getVolume()}" id="vol-brown" />
          <button class="btn ${soundEngine.isPlaying('brown') ? 'btn-danger' : 'btn-secondary'}" data-sound="brown" id="btn-sound-brown">
            <span>${soundEngine.isPlaying('brown') ? 'Stop' : 'Play'}</span>
          </button>
        </div>
      </div>

      <!-- Rain Ambience -->
      <div class="soundscape-row">
        <div class="soundscape-info">
          <span class="soundscape-title">Gentle Rain Ambience</span>
          <span class="soundscape-desc">Organic filtered precipitation pattern creating an immersive natural sound cocoon.</span>
        </div>
        <div class="soundscape-actions">
          <div class="audio-visualizer ${soundEngine.isPlaying('rain') ? 'playing' : ''}" id="vis-rain">
            <span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span><span class="audio-bar"></span>
          </div>
          <input type="range" class="volume-slider" min="0" max="1" step="0.05" value="${soundEngine.getVolume()}" id="vol-rain" />
          <button class="btn ${soundEngine.isPlaying('rain') ? 'btn-danger' : 'btn-secondary'}" data-sound="rain" id="btn-sound-rain">
            <span>${soundEngine.isPlaying('rain') ? 'Stop' : 'Play'}</span>
          </button>
        </div>
      </div>
    </div>
  `;

  // Attach Sprint Tabs
  document.querySelectorAll<HTMLButtonElement>('.sprint-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      if (isSprintRunning) return; // Prevent changing mode while running
      document.querySelectorAll('.sprint-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const mins = parseInt(tab.dataset.mins || '25', 10);
      sprintTotalSeconds = mins * 60;
      sprintRemainingSeconds = sprintTotalSeconds;
      const timerDisplay = document.getElementById('sprint-timer-text');
      if (timerDisplay) timerDisplay.textContent = formatSeconds(sprintRemainingSeconds);
    });
  });

  // Attach Sprint Controls
  const toggleBtn = document.getElementById('sprint-toggle-btn');
  const resetBtn = document.getElementById('sprint-reset-btn');

  toggleBtn?.addEventListener('click', () => {
    if (isSprintRunning) {
      pauseSprint();
    } else {
      startSprint();
    }
  });

  resetBtn?.addEventListener('click', () => {
    resetSprint();
  });

  // Attach Soundscape Controls
  setupSoundscapeButtons();
}

function startSprint() {
  isSprintRunning = true;
  const toggleBtn = document.getElementById('sprint-toggle-btn');
  const statusNote = document.getElementById('sprint-status-note');
  if (toggleBtn) toggleBtn.innerHTML = '<span>⏸️ Pause</span>';
  if (statusNote) statusNote.textContent = 'Deep Focus Session In Progress — Distractions Shielded';

  playTone(440, 0.15);

  sprintTimerInterval = window.setInterval(() => {
    sprintRemainingSeconds--;
    const timerDisplay = document.getElementById('sprint-timer-text');
    if (timerDisplay) timerDisplay.textContent = formatSeconds(sprintRemainingSeconds);

    if (sprintRemainingSeconds <= 0) {
      completeSprint();
    }
  }, 1000);
}

function pauseSprint() {
  isSprintRunning = false;
  if (sprintTimerInterval) clearInterval(sprintTimerInterval);
  sprintTimerInterval = null;

  const toggleBtn = document.getElementById('sprint-toggle-btn');
  const statusNote = document.getElementById('sprint-status-note');
  if (toggleBtn) toggleBtn.innerHTML = '<span>▶️ Resume</span>';
  if (statusNote) statusNote.textContent = 'Session paused. Ready to continue.';
}

function resetSprint() {
  pauseSprint();
  sprintRemainingSeconds = sprintTotalSeconds;
  const timerDisplay = document.getElementById('sprint-timer-text');
  const toggleBtn = document.getElementById('sprint-toggle-btn');
  if (timerDisplay) timerDisplay.textContent = formatSeconds(sprintRemainingSeconds);
  if (toggleBtn) toggleBtn.innerHTML = '<span>▶️ Begin Sprint</span>';
}

async function completeSprint() {
  pauseSprint();
  sprintRemainingSeconds = sprintTotalSeconds;

  // Sound chime
  playTone(587.33, 0.4);
  setTimeout(() => playTone(880, 0.6), 250);

  // Confetti Blast!
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#7EE7C6', '#6366F1', '#34D399', '#FBBF24'],
  });

  // Log to backend
  try {
    await api.logFocusSession(sprintTotalSeconds);
    await fetchLatestStatus();
  } catch (e) {
    console.error('Failed to log sprint', e);
  }

  const timerDisplay = document.getElementById('sprint-timer-text');
  const statusNote = document.getElementById('sprint-status-note');
  if (timerDisplay) timerDisplay.textContent = formatSeconds(sprintRemainingSeconds);
  if (statusNote) statusNote.textContent = '🎉 Sprint Complete! Logged to your daily focus record.';
}

function setupSoundscapeButtons() {
  ['alpha', 'brown', 'rain'].forEach((type) => {
    const btn = document.getElementById(`btn-sound-${type}`);
    const slider = document.getElementById(`vol-${type}`) as HTMLInputElement | null;
    const vis = document.getElementById(`vis-${type}`);

    btn?.addEventListener('click', () => {
      if (soundEngine.isPlaying(type)) {
        soundEngine.stop();
        refreshSoundUi();
      } else {
        soundEngine.play(type as 'alpha' | 'brown' | 'rain');
        refreshSoundUi();
      }
    });

    slider?.addEventListener('input', () => {
      soundEngine.setVolume(parseFloat(slider.value));
    });
  });

  document.getElementById('soundscape-stop-all')?.addEventListener('click', () => {
    soundEngine.stop();
    refreshSoundUi();
  });
}

function refreshSoundUi() {
  ['alpha', 'brown', 'rain'].forEach((type) => {
    const btn = document.getElementById(`btn-sound-${type}`);
    const vis = document.getElementById(`vis-${type}`);
    const playing = soundEngine.isPlaying(type);

    if (btn) {
      btn.className = `btn ${playing ? 'btn-danger' : 'btn-secondary'}`;
      btn.innerHTML = `<span>${playing ? 'Stop' : 'Play'}</span>`;
    }
    if (vis) {
      vis.className = `audio-visualizer ${playing ? 'playing' : ''}`;
    }
  });
}

// --------------------------------------------------------------------------
// 3. COGNITIVE INSIGHTS PAGE
// --------------------------------------------------------------------------
async function renderInsights(container: HTMLElement) {
  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Cognitive Insights & Recommendations</h1>
        <p class="page-subtitle">Algorithmic analysis of your work habits, context switching penalties, and peak productivity windows.</p>
      </div>
      <button class="btn btn-secondary" id="insights-refresh-btn">
        <span>🔄 Re-analyze</span>
      </button>
    </div>
    <div id="insights-list-container" style="display:flex; flex-direction:column; gap:16px;">
      <div style="text-align:center; padding:40px; color:var(--text-muted);">
        Analyzing cognitive database...
      </div>
    </div>
  `;

  document.getElementById('insights-refresh-btn')?.addEventListener('click', () => renderInsights(container));

  try {
    const res = await api.getInsights();
    const listContainer = document.getElementById('insights-list-container');
    if (!listContainer) return;

    if (!res.insights || res.insights.length === 0) {
      listContainer.innerHTML = `
        <div class="glass-card" style="text-align:center; padding:48px 24px;">
          <span style="font-size:36px; display:block; margin-bottom:12px;">🌱</span>
          <h3 style="font-size:17px; font-weight:700;">Building Baseline Profile</h3>
          <p style="color:var(--text-secondary); font-size:13.5px; max-width:440px; margin:8px auto 0 auto;">
            Continue using your system normally. As sessions accumulate in <code>cognitive.db</code>, personalized circadian insights will populate here.
          </p>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = res.insights
      .map((item: InsightItem) => {
        const isUrgent = item.urgency === 'high';
        return `
          <div class="glass-card" style="border-left: 4px solid ${isUrgent ? 'var(--accent-coral)' : 'var(--accent-iris)'};">
            <div class="tile-top" style="margin-bottom:8px;">
              <span class="tile-label" style="color:${isUrgent ? 'var(--accent-coral)' : 'var(--accent-iris)'};">${item.type.toUpperCase()}</span>
              <span class="pill-category">${item.impact || 'Productivity Gain'}</span>
            </div>
            <h3 style="font-size:16px; font-weight:700; margin-bottom:6px;">${item.title}</h3>
            <p style="font-size:13.5px; color:var(--text-secondary); line-height:1.6;">${item.message}</p>
          </div>
        `;
      })
      .join('');
  } catch (err) {
    console.error('Insights error', err);
  }
}

// --------------------------------------------------------------------------
// 4. DEEP ANALYTICS PAGE
// --------------------------------------------------------------------------
async function renderAnalytics(container: HTMLElement, days = 7) {
  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Deep Behavioral Analytics</h1>
        <p class="page-subtitle">Historical screen time trends, software category distributions, and cognitive strain analysis.</p>
      </div>
      <div style="display:flex; gap:10px;">
        <div class="sprint-mode-tabs" style="margin:0;">
          <button class="sprint-tab ${days === 1 ? 'active' : ''}" data-days="1">1 Day</button>
          <button class="sprint-tab ${days === 7 ? 'active' : ''}" data-days="7">7 Days</button>
          <button class="sprint-tab ${days === 30 ? 'active' : ''}" data-days="30">30 Days</button>
        </div>
        <button class="btn btn-secondary" id="analytics-export-btn">
          <span>📥 Export Data</span>
        </button>
      </div>
    </div>

    <div id="analytics-loading" style="text-align:center; padding:50px; color:var(--text-muted);">
      Loading analytics metrics...
    </div>

    <div id="analytics-content" class="hidden">
      <!-- Daily Trend Chart -->
      <div class="glass-card" style="margin-bottom:24px;">
        <div class="tile-top" style="margin-bottom:16px;">
          <div>
            <span class="tile-label">Daily Focus Time</span>
            <h3 style="font-size:16px; font-weight:700;">Recorded Screen Time (Minutes / Day)</h3>
          </div>
        </div>
        <div id="analytics-chart-container" style="height:200px; display:flex; align-items:flex-end; gap:16px; padding-top:20px;">
          <!-- Injected dynamically -->
        </div>
      </div>

      <!-- Categories & Top Apps Grid -->
      <div class="grid-cols-2">
        <!-- Categories Breakdown -->
        <div class="glass-card">
          <div class="tile-top" style="margin-bottom:16px;">
            <span class="tile-label">Category Time Distribution</span>
          </div>
          <div id="analytics-categories-list" style="display:flex; flex-direction:column; gap:12px;">
            <!-- Categories injected -->
          </div>
        </div>

        <!-- Top Applications -->
        <div class="glass-card">
          <div class="tile-top" style="margin-bottom:16px;">
            <span class="tile-label">Top Software & Focus Ratings</span>
          </div>
          <div id="analytics-apps-list" style="display:flex; flex-direction:column; gap:10px;">
            <!-- Apps injected -->
          </div>
        </div>
      </div>
    </div>
  `;

  // Attach Day Selector Tabs
  container.querySelectorAll<HTMLButtonElement>('.sprint-mode-tabs .sprint-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      const d = parseInt(tab.dataset.days || '7', 10);
      renderAnalytics(container, d);
    });
  });

  try {
    const data: AnalyticsData = await api.getAnalytics(days);
    const loading = document.getElementById('analytics-loading');
    const content = document.getElementById('analytics-content');
    loading?.classList.add('hidden');
    content?.classList.remove('hidden');

    // Render Daily Bar Chart
    const chartContainer = document.getElementById('analytics-chart-container');
    if (chartContainer && data.daily.length > 0) {
      const maxMins = Math.max(...data.daily.map((d) => d.minutes), 60);
      chartContainer.innerHTML = data.daily
        .map((item) => {
          const heightPercent = Math.max(10, Math.round((item.minutes / maxMins) * 100));
          return `
            <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:8px;">
              <span style="font-size:11px; font-family:var(--font-mono); color:var(--text-secondary);">${item.minutes}m</span>
              <div style="width:100%; max-width:42px; height:${heightPercent}%; background:linear-gradient(180deg, var(--accent-iris), #312E81); border-radius:6px 6px 0 0; box-shadow:0 0 10px rgba(99,102,241,0.2);"></div>
              <span style="font-size:11px; color:var(--text-muted);">${item.date.split('-').slice(1).join('/')}</span>
            </div>
          `;
        })
        .join('');
    } else if (chartContainer) {
      chartContainer.innerHTML = `<div style="margin:auto; color:var(--text-muted); font-size:13px;">No session records logged in this timeframe.</div>`;
    }

    // Render Category Distribution
    const catList = document.getElementById('analytics-categories-list');
    if (catList && data.categories.length > 0) {
      const totalSec = data.categories.reduce((acc, c) => acc + c.duration_sec, 0) || 1;
      catList.innerHTML = data.categories
        .map((cat) => {
          const pct = Math.round((cat.duration_sec / totalSec) * 100);
          return `
            <div>
              <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:600; margin-bottom:4px;">
                <span>${cat.category}</span>
                <span style="color:var(--text-secondary); font-family:var(--font-mono);">${formatHoursAndMins(cat.duration_sec)} (${pct}%)</span>
              </div>
              <div style="height:6px; background:rgba(255,255,255,0.06); border-radius:3px; overflow:hidden;">
                <div style="width:${pct}%; height:100%; background:var(--accent-teal); border-radius:3px;"></div>
              </div>
            </div>
          `;
        })
        .join('');
    } else if (catList) {
      catList.innerHTML = `<div style="color:var(--text-muted); font-size:13px;">No categorized session data.</div>`;
    }

    // Render Apps Leaderboard
    const appList = document.getElementById('analytics-apps-list');
    if (appList && data.apps.length > 0) {
      appList.innerHTML = data.apps
        .map((app) => {
          const col = getFocusColor(app.focus_score);
          return `
            <div class="activity-item">
              <div>
                <span class="activity-app-name">${app.app}</span>
                <span class="activity-duration" style="margin-left:8px;">${formatHoursAndMins(app.duration_sec)}</span>
              </div>
              <span style="font-size:11.5px; font-weight:700; color:${col}; background:${col}18; padding:3px 8px; border-radius:var(--radius-full);">
                ${app.focus_score} Score
              </span>
            </div>
          `;
        })
        .join('');
    } else if (appList) {
      appList.innerHTML = `<div style="color:var(--text-muted); font-size:13px;">No applications tracked yet.</div>`;
    }

    // Attach Export Action
    document.getElementById('analytics-export-btn')?.addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cognitive-analytics-${days}d.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  } catch (err) {
    console.error('Analytics load error', err);
  }
}

// --------------------------------------------------------------------------
// 5. AI COACH PAGE
// --------------------------------------------------------------------------
async function renderAiCoach(container: HTMLElement) {
  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">AI Cognitive Coach</h1>
        <p class="page-subtitle">Your private neural performance mentor. Ask questions about your energy rhythm, recovery, and focus habits.</p>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-messages" id="chat-messages-box">
        <div class="chat-bubble ai">
          👋 Hello! I am your Cognitive AI Coach. I continuously analyze your active foreground applications, context switching velocity, and mental fatigue parameters. How can I assist you with your focus or mental recovery today?
        </div>
      </div>

      <!-- Quick Suggested Prompt Chips -->
      <div class="quick-prompts-row">
        <button class="prompt-chip" data-prompt="How can I recover quickly from high cognitive fatigue?">⚡ Quick Fatigue Reset</button>
        <button class="prompt-chip" data-prompt="Analyze my work pattern today and recommend a schedule.">📅 Recommend Schedule</button>
        <button class="prompt-chip" data-prompt="What causes context switching penalties on my focus?">🧠 Context Switch Penalties</button>
        <button class="prompt-chip" data-prompt="Give me a 3-minute mental relaxation routine.">🌬️ 3-Minute Mental Routine</button>
      </div>

      <!-- Chat Input Field -->
      <div class="chat-input-row">
        <input type="text" class="chat-input" id="chat-user-input" placeholder="Ask your AI coach anything..." />
        <button class="btn btn-primary" id="chat-send-btn">
          <span>Send</span>
        </button>
      </div>
    </div>
  `;

  const messagesBox = document.getElementById('chat-messages-box');
  const input = document.getElementById('chat-user-input') as HTMLInputElement | null;
  const sendBtn = document.getElementById('chat-send-btn');

  // Load chat history from backend
  try {
    const historyRes = await api.getChatHistory();
    if (historyRes.history && historyRes.history.length > 0 && messagesBox) {
      historyRes.history.slice(-10).forEach((msg: ChatMessage) => {
        appendChatBubble(messagesBox, msg.user_prompt, 'user');
        appendChatBubble(messagesBox, msg.ai_response, 'ai');
      });
    }
  } catch (err) {
    console.warn('Chat history error', err);
  }

  const handleSend = async () => {
    if (!input || !messagesBox) return;
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    appendChatBubble(messagesBox, text, 'user');

    // Show typing placeholder
    const typingBubble = appendChatBubble(messagesBox, '🧠 Analyzing cognitive telemetry...', 'ai');

    try {
      const res = await api.sendChatMessage(text);
      typingBubble.textContent = res.reply;
      playTone(600, 0.1);
    } catch {
      typingBubble.textContent = 'Unable to reach cognitive companion engine. Please check backend connection.';
    }
  };

  sendBtn?.addEventListener('click', handleSend);
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSend();
  });

  // Prompt chips
  document.querySelectorAll<HTMLButtonElement>('.prompt-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      if (input) {
        input.value = chip.dataset.prompt || '';
        handleSend();
      }
    });
  });
}

function appendChatBubble(container: HTMLElement, text: string, sender: 'user' | 'ai'): HTMLElement {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;
  bubble.textContent = text;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  return bubble;
}

// --------------------------------------------------------------------------
// 6. STREAKS & GOALS PAGE
// --------------------------------------------------------------------------
function renderStreaks(container: HTMLElement) {
  const status = systemStatus || {
    streak: 1,
    deep_work_sec: 3600,
    distraction_count: 5,
    goal_focus_hours: 5,
    goal_distraction_mins: 60,
    goal_screen_time_hours: 8,
  };

  const focusHours = (status.deep_work_sec / 3600);
  const focusGoal = status.goal_focus_hours || 5;
  const focusProgressPct = Math.min(100, Math.round((focusHours / focusGoal) * 100));

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Goals, Habits & Milestone Streaks</h1>
        <p class="page-subtitle">Track your deep work discipline, consistency records, and unlocked cognitive mastery badges.</p>
      </div>
    </div>

    <!-- Active Streak Banner -->
    <div class="glass-card" style="margin-bottom:24px; background:radial-gradient(circle at 10% 50%, rgba(245, 158, 11, 0.15) 0%, transparent 60%), var(--bg-card); display:flex; align-items:center; justify-content:space-between;">
      <div style="display:flex; align-items:center; gap:20px;">
        <span style="font-size:48px;">🔥</span>
        <div>
          <span class="tile-label" style="color:var(--accent-amber);">CURRENT STREAK</span>
          <h2 style="font-size:32px; font-weight:800; letter-spacing:-0.5px;">${status.streak} Consecutive Days</h2>
          <p style="font-size:13px; color:var(--text-secondary); margin-top:2px;">Complete at least 1 focus sprint today to keep your streak burning bright!</p>
        </div>
      </div>
      <button class="btn btn-primary" id="streak-sprint-btn">
        <span>⚡ Continue Streak</span>
      </button>
    </div>

    <!-- Daily Goal Progress -->
    <div class="grid-cols-2">
      <div class="glass-card">
        <div class="tile-top" style="margin-bottom:12px;">
          <span class="tile-label">Daily Focus Target</span>
          <span style="font-weight:700; color:var(--accent-teal);">${focusHours.toFixed(1)} / ${focusGoal}.0 hrs</span>
        </div>
        <div style="height:10px; background:rgba(255,255,255,0.06); border-radius:5px; overflow:hidden; margin-bottom:12px;">
          <div style="width:${focusProgressPct}%; height:100%; background:linear-gradient(90deg, var(--accent-teal), var(--accent-iris)); border-radius:5px;"></div>
        </div>
        <span class="tile-sub">${focusProgressPct}% completed towards your target deep work quota.</span>
      </div>

      <div class="glass-card">
        <div class="tile-top" style="margin-bottom:12px;">
          <span class="tile-label">Context Switch Threshold</span>
          <span style="font-weight:700; color:${status.distraction_count > 15 ? 'var(--accent-coral)' : 'var(--accent-emerald)'};">${status.distraction_count} switches</span>
        </div>
        <div style="height:10px; background:rgba(255,255,255,0.06); border-radius:5px; overflow:hidden; margin-bottom:12px;">
          <div style="width:${Math.min(100, (status.distraction_count / 20) * 100)}%; height:100%; background:${status.distraction_count > 15 ? 'var(--accent-coral)' : 'var(--accent-emerald)'}; border-radius:5px;"></div>
        </div>
        <span class="tile-sub">Target: keep below 15 task switches to protect working memory.</span>
      </div>
    </div>

    <!-- Achievement Badges -->
    <div class="glass-card">
      <div class="tile-top" style="margin-bottom:16px;">
        <span class="tile-label">Cognitive Mastery Achievements</span>
      </div>
      <div class="grid-cols-4" style="margin:0;">
        <div class="glass-card" style="text-align:center; padding:16px; border-color:${status.streak >= 1 ? 'rgba(245, 158, 11, 0.4)' : 'var(--border-subtle)'};">
          <span style="font-size:28px; display:block; margin-bottom:8px;">🥉</span>
          <span style="font-weight:700; font-size:13.5px; display:block;">Pioneer Spark</span>
          <span style="font-size:11px; color:var(--text-muted);">1-Day Active Streak</span>
          <span style="font-size:10px; font-weight:700; color:var(--accent-amber); display:block; margin-top:6px;">UNLOCKED</span>
        </div>

        <div class="glass-card" style="text-align:center; padding:16px; border-color:${status.streak >= 7 ? 'rgba(99, 102, 241, 0.4)' : 'var(--border-subtle)'}; opacity:${status.streak >= 7 ? '1' : '0.5'};">
          <span style="font-size:28px; display:block; margin-bottom:8px;">🥈</span>
          <span style="font-weight:700; font-size:13.5px; display:block;">Deep Worker</span>
          <span style="font-size:11px; color:var(--text-muted);">7-Day Streak</span>
          <span style="font-size:10px; font-weight:700; color:${status.streak >= 7 ? 'var(--accent-iris)' : 'var(--text-muted)'}; display:block; margin-top:6px;">${status.streak >= 7 ? 'UNLOCKED' : 'LOCKED'}</span>
        </div>

        <div class="glass-card" style="text-align:center; padding:16px; border-color:${status.streak >= 30 ? 'rgba(126, 231, 198, 0.4)' : 'var(--border-subtle)'}; opacity:${status.streak >= 30 ? '1' : '0.5'};">
          <span style="font-size:28px; display:block; margin-bottom:8px;">🥇</span>
          <span style="font-weight:700; font-size:13.5px; display:block;">Focus Monk</span>
          <span style="font-size:11px; color:var(--text-muted);">30-Day Streak</span>
          <span style="font-size:10px; font-weight:700; color:${status.streak >= 30 ? 'var(--accent-teal)' : 'var(--text-muted)'}; display:block; margin-top:6px;">${status.streak >= 30 ? 'UNLOCKED' : 'LOCKED'}</span>
        </div>

        <div class="glass-card" style="text-align:center; padding:16px; border-color:${focusHours >= 5 ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-subtle)'}; opacity:${focusHours >= 5 ? '1' : '0.5'};">
          <span style="font-size:28px; display:block; margin-bottom:8px;">💎</span>
          <span style="font-weight:700; font-size:13.5px; display:block;">Zenith Titan</span>
          <span style="font-size:11px; color:var(--text-muted);">5+ Hours Daily Focus</span>
          <span style="font-size:10px; font-weight:700; color:${focusHours >= 5 ? 'var(--accent-emerald)' : 'var(--text-muted)'}; display:block; margin-top:6px;">${focusHours >= 5 ? 'UNLOCKED' : 'IN PROGRESS'}</span>
        </div>
      </div>
    </div>
  `;

  document.getElementById('streak-sprint-btn')?.addEventListener('click', () => navigateTo('focus'));
}

// --------------------------------------------------------------------------
// 7. AUDIT LOG & NOTIFICATIONS PAGE
// --------------------------------------------------------------------------
async function renderNotifications(container: HTMLElement) {
  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">Cognitive Audit Log & Notifications</h1>
        <p class="page-subtitle">Auditable record of fatigue alerts, sprint completions, and system events.</p>
      </div>
      <button class="btn btn-danger" id="notif-clear-btn">
        <span>🗑️ Clear History</span>
      </button>
    </div>

    <div class="glass-card">
      <div id="notif-list-container" style="display:flex; flex-direction:column; gap:10px;">
        <div style="text-align:center; padding:30px; color:var(--text-muted);">
          Loading notification logs...
        </div>
      </div>
    </div>
  `;

  const list = document.getElementById('notif-list-container');

  try {
    const res = await api.getNotifications();
    const countBadge = document.getElementById('sidebar-notif-count');
    if (countBadge) countBadge.textContent = (res.notifications?.length || 0).toString();

    if (!res.notifications || res.notifications.length === 0) {
      if (list) list.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-muted); font-size:13.5px;">No events in audit log. System operating normally.</div>`;
      return;
    }

    if (list) {
      list.innerHTML = res.notifications
        .map((n: NotificationItem) => {
          let badgeClass = 'text-teal';
          let icon = 'ℹ️';
          if (n.type.toLowerCase().includes('alert')) {
            badgeClass = 'text-coral';
            icon = '⚠️';
          } else if (n.type.toLowerCase().includes('focus')) {
            badgeClass = 'text-iris';
            icon = '🎯';
          } else if (n.type.toLowerCase().includes('break')) {
            badgeClass = 'text-emerald';
            icon = '🌬️';
          }

          return `
            <div class="activity-item">
              <div style="display:flex; align-items:center; gap:12px;">
                <span>${icon}</span>
                <div>
                  <span style="font-weight:600; font-size:13.5px;">${n.message}</span>
                  <span class="activity-category-tag" style="margin-left:8px;">${n.type}</span>
                </div>
              </div>
              <span class="activity-duration">${n.timestamp ? n.timestamp.split('T').join(' ').split('.')[0] : ''}</span>
            </div>
          `;
        })
        .join('');
    }

    document.getElementById('notif-clear-btn')?.addEventListener('click', async () => {
      await api.clearNotifications();
      renderNotifications(container);
    });
  } catch (err) {
    console.error('Notif error', err);
  }
}

// --------------------------------------------------------------------------
// 8. SETTINGS PAGE
// --------------------------------------------------------------------------
async function renderSettings(container: HTMLElement) {
  let settings: AppSettings = {
    goal_focus_hours: 5,
    goal_distraction_mins: 60,
    goal_screen_time_hours: 8,
    autostart: true,
    sound_effects: true,
  };

  try {
    settings = await api.getSettings();
  } catch (e) {
    console.warn('Failed to load settings', e);
  }

  container.innerHTML = `
    <div class="page-header">
      <div>
        <h1 class="page-title">System Settings & Calibration</h1>
        <p class="page-subtitle">Configure your productivity quotas, background tracking parameters, and notification thresholds.</p>
      </div>
      <button class="btn btn-success" id="settings-save-btn">
        <span>💾 Save Configuration</span>
      </button>
    </div>

    <div class="grid-cols-2">
      <!-- Focus Targets -->
      <div class="glass-card" style="display:flex; flex-direction:column; gap:16px;">
        <span class="tile-label">Cognitive Targets</span>
        
        <div>
          <label style="display:block; font-size:13px; font-weight:600; margin-bottom:6px;">Daily Deep Work Goal (Hours)</label>
          <input type="number" id="setting-focus-hours" value="${settings.goal_focus_hours || 5}" min="1" max="16" class="chat-input" style="width:100%;" />
        </div>

        <div>
          <label style="display:block; font-size:13px; font-weight:600; margin-bottom:6px;">Distraction Threshold (Minutes)</label>
          <input type="number" id="setting-distraction-mins" value="${settings.goal_distraction_mins || 60}" min="10" max="240" class="chat-input" style="width:100%;" />
        </div>

        <div>
          <label style="display:block; font-size:13px; font-weight:600; margin-bottom:6px;">Maximum Screen Time Quota (Hours)</label>
          <input type="number" id="setting-screen-hours" value="${settings.goal_screen_time_hours || 8}" min="2" max="18" class="chat-input" style="width:100%;" />
        </div>
      </div>

      <!-- App Behavior & Info -->
      <div class="glass-card" style="display:flex; flex-direction:column; gap:16px;">
        <span class="tile-label">Engine Telemetry & Privacy</span>

        <div style="display:flex; align-items:center; justify-content:space-between; padding:12px; background:rgba(255,255,255,0.02); border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
          <div>
            <span style="font-weight:600; font-size:13.5px; display:block;">Local Zero-Cloud Storage</span>
            <span style="font-size:11.5px; color:var(--text-muted);">All window titles and metrics remain 100% on your machine in SQLite.</span>
          </div>
          <span style="color:var(--accent-teal); font-weight:700; font-size:12px;">ACTIVE</span>
        </div>

        <div style="display:flex; align-items:center; justify-content:space-between; padding:12px; background:rgba(255,255,255,0.02); border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
          <div>
            <span style="font-weight:600; font-size:13.5px; display:block;">Acoustic Audio Feedback</span>
            <span style="font-size:11.5px; color:var(--text-muted);">Chimes upon focus completion and mindful break transitions.</span>
          </div>
          <input type="checkbox" id="setting-sound" ${settings.sound_effects !== false ? 'checked' : ''} style="width:18px; height:18px; accent-color:var(--accent-iris);" />
        </div>

        <div style="padding:12px; background:rgba(255,255,255,0.02); border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
          <span style="font-size:12px; color:var(--text-muted); display:block;">Bridge Endpoint:</span>
          <code style="font-family:var(--font-mono); font-size:12px; color:var(--accent-teal);">http://127.0.0.1:8765</code>
        </div>
      </div>
    </div>
  `;

  document.getElementById('settings-save-btn')?.addEventListener('click', async () => {
    const focusH = parseFloat((document.getElementById('setting-focus-hours') as HTMLInputElement).value);
    const distM = parseInt((document.getElementById('setting-distraction-mins') as HTMLInputElement).value, 10);
    const screenH = parseFloat((document.getElementById('setting-screen-hours') as HTMLInputElement).value);
    const sound = (document.getElementById('setting-sound') as HTMLInputElement).checked;

    try {
      await api.saveSettings({
        goal_focus_hours: focusH,
        goal_distraction_mins: distM,
        goal_screen_time_hours: screenH,
        sound_effects: sound,
      });
      playTone(520, 0.2);
      alert('Settings saved successfully.');
    } catch (e) {
      alert('Failed to save settings.');
    }
  });
}

// ==========================================================================
// 9. GUIDED 4-7-8 MINDFUL BREATHING MODAL
// ==========================================================================
function setupBreathingModal() {
  const modal = document.getElementById('breathing-modal');
  const closeBtn = document.getElementById('breathing-close-btn');
  const cancelBtn = document.getElementById('breathing-cancel-btn');
  const startBtn = document.getElementById('breathing-start-btn');
  const completeBtn = document.getElementById('breathing-complete-btn');

  const close = () => {
    stopBreathing();
    modal?.classList.add('hidden');
  };

  closeBtn?.addEventListener('click', close);
  cancelBtn?.addEventListener('click', close);

  startBtn?.addEventListener('click', () => {
    startBreathingCycle();
  });

  completeBtn?.addEventListener('click', async () => {
    close();
    try {
      await api.completeBreak();
      fetchLatestStatus();
      confetti({ particleCount: 60, spread: 50, origin: { y: 0.7 } });
    } catch (e) {
      console.error(e);
    }
  });
}

function openBreathingModal() {
  const modal = document.getElementById('breathing-modal');
  modal?.classList.remove('hidden');
  resetBreathingUi();
}

function resetBreathingUi() {
  stopBreathing();
  breathingCycle = 1;
  const circle = document.getElementById('breathing-circle');
  const phaseText = document.getElementById('breath-phase-text');
  const counterText = document.getElementById('breath-counter-text');
  const cycleCount = document.getElementById('breath-cycle-count');
  const startBtn = document.getElementById('breathing-start-btn');
  const completeBtn = document.getElementById('breathing-complete-btn');

  if (circle) circle.className = 'breathing-circle-outer';
  if (phaseText) phaseText.textContent = 'Ready';
  if (counterText) counterText.textContent = '4s';
  if (cycleCount) cycleCount.textContent = '1 of 4';
  startBtn?.classList.remove('hidden');
  completeBtn?.classList.add('hidden');
}

function stopBreathing() {
  if (breathingInterval) {
    clearInterval(breathingInterval);
    breathingInterval = null;
  }
}

function startBreathingCycle() {
  const startBtn = document.getElementById('breathing-start-btn');
  startBtn?.classList.add('hidden');

  breathingCycle = 1;
  runInhale();
}

function runInhale() {
  breathingPhase = 'inhale';
  breathingSecondsLeft = 4;
  updateBreathingStep('Inhale Deeply (Nose)', 'inhale', 4);
  playTone(261.63, 0.5); // C4

  breathingInterval = window.setInterval(() => {
    breathingSecondsLeft--;
    setCounterText(`${breathingSecondsLeft}s`);
    if (breathingSecondsLeft <= 0) {
      clearInterval(breathingInterval!);
      runHold();
    }
  }, 1000);
}

function runHold() {
  breathingPhase = 'hold';
  breathingSecondsLeft = 7;
  updateBreathingStep('Hold Breath', 'hold', 7);
  playTone(329.63, 0.4); // E4

  breathingInterval = window.setInterval(() => {
    breathingSecondsLeft--;
    setCounterText(`${breathingSecondsLeft}s`);
    if (breathingSecondsLeft <= 0) {
      clearInterval(breathingInterval!);
      runExhale();
    }
  }, 1000);
}

function runExhale() {
  breathingPhase = 'exhale';
  breathingSecondsLeft = 8;
  updateBreathingStep('Exhale Smoothly (Mouth)', 'exhale', 8);
  playTone(196.0, 0.6); // G3

  breathingInterval = window.setInterval(() => {
    breathingSecondsLeft--;
    setCounterText(`${breathingSecondsLeft}s`);
    if (breathingSecondsLeft <= 0) {
      clearInterval(breathingInterval!);
      breathingCycle++;
      const cycleCount = document.getElementById('breath-cycle-count');
      if (cycleCount) cycleCount.textContent = `${Math.min(breathingCycle, 4)} of 4`;

      if (breathingCycle <= TOTAL_BREATHING_CYCLES) {
        runInhale();
      } else {
        finishBreathing();
      }
    }
  }, 1000);
}

function updateBreathingStep(label: string, cssClass: string, startSec: number) {
  const circle = document.getElementById('breathing-circle');
  const phaseText = document.getElementById('breath-phase-text');
  if (circle) circle.className = `breathing-circle-outer ${cssClass}`;
  if (phaseText) phaseText.textContent = label;
  setCounterText(`${startSec}s`);
}

function setCounterText(text: string) {
  const counterText = document.getElementById('breath-counter-text');
  if (counterText) counterText.textContent = text;
}

function finishBreathing() {
  stopBreathing();
  const phaseText = document.getElementById('breath-phase-text');
  const counterText = document.getElementById('breath-counter-text');
  const completeBtn = document.getElementById('breathing-complete-btn');

  if (phaseText) phaseText.textContent = 'Session Complete';
  if (counterText) counterText.textContent = '🌿';
  completeBtn?.classList.remove('hidden');

  playTone(523.25, 0.8); // C5
}

// ==========================================================================
// 10. COMMAND PALETTE (CTRL+K)
// ==========================================================================
const COMMANDS = [
  { id: 'dash', title: 'Open Dashboard', shortcut: '⚡', action: () => navigateTo('dashboard') },
  { id: 'focus', title: 'Start Focus Sprint & Audio', shortcut: '🎯', action: () => navigateTo('focus') },
  { id: 'insights', title: 'View Cognitive Insights', shortcut: '💡', action: () => navigateTo('insights') },
  { id: 'analytics', title: 'Deep Behavioral Analytics', shortcut: '📊', action: () => navigateTo('analytics') },
  { id: 'coach', title: 'Consult AI Cognitive Coach', shortcut: '🤖', action: () => navigateTo('coach') },
  { id: 'streaks', title: 'Habit Streaks & Goals', shortcut: '🏆', action: () => navigateTo('streaks') },
  { id: 'notifs', title: 'View Audit Log & Alerts', shortcut: '🔔', action: () => navigateTo('notifications') },
  { id: 'settings', title: 'System Settings', shortcut: '⚙️', action: () => navigateTo('settings') },
  { id: 'breathe', title: 'Take 4-7-8 Mindful Breath Break', shortcut: '🌬️', action: () => openBreathingModal() },
  { id: 'shield', title: 'Toggle Focus Shield', shortcut: '🛡️', action: () => document.getElementById('focus-shield-toggle')?.click() },
];

function setupCommandPalette() {
  const modal = document.getElementById('cmd-palette-modal');
  const trigger = document.getElementById('cmd-palette-btn');
  const input = document.getElementById('cmd-palette-input') as HTMLInputElement | null;
  const results = document.getElementById('cmd-results-list');

  const open = () => {
    modal?.classList.remove('hidden');
    if (input) {
      input.value = '';
      input.focus();
    }
    renderFilteredCommands('');
  };

  const close = () => {
    modal?.classList.add('hidden');
  };

  trigger?.addEventListener('click', open);

  // Keyboard shortcut Ctrl+K or Cmd+K
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (modal?.classList.contains('hidden')) {
        open();
      } else {
        close();
      }
    }
    if (e.key === 'Escape') {
      close();
    }
  });

  input?.addEventListener('input', () => {
    renderFilteredCommands(input.value.trim().toLowerCase());
  });

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) close();
  });

  function renderFilteredCommands(filter: string) {
    if (!results) return;
    const filtered = COMMANDS.filter((c) => c.title.toLowerCase().includes(filter));
    if (filtered.length === 0) {
      results.innerHTML = `<div style="padding:14px; text-align:center; color:var(--text-muted); font-size:13px;">No matching commands.</div>`;
      return;
    }

    results.innerHTML = filtered
      .map(
        (c, idx) => `
        <div class="cmd-item ${idx === 0 ? 'selected' : ''}" data-cmd-id="${c.id}">
          <div style="display:flex; align-items:center; gap:10px;">
            <span>${c.shortcut}</span>
            <span>${c.title}</span>
          </div>
          <span class="cmd-item-shortcut">Jump</span>
        </div>
      `
      )
      .join('');

    results.querySelectorAll<HTMLElement>('.cmd-item').forEach((item) => {
      item.addEventListener('click', () => {
        const cmd = COMMANDS.find((c) => c.id === item.dataset.cmdId);
        if (cmd) {
          close();
          cmd.action();
        }
      });
    });
  }
}
