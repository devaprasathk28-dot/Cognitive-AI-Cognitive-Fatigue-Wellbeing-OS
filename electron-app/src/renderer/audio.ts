// High-fidelity Web Audio Synthesizer for Ambient Cognitive Focus Soundscapes

class AmbientAudioEngine {
  private ctx: AudioContext | null = null;
  private currentType: string | null = null;
  private gainNode: GainNode | null = null;
  private activeSourceNodes: (AudioNode | number)[] = [];
  private volume: number = 0.5;

  private initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public setVolume(val: number) {
    this.volume = Math.max(0, Math.min(1, val));
    if (this.gainNode && this.ctx) {
      this.gainNode.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.05);
    }
  }

  public getVolume(): number {
    return this.volume;
  }

  public isPlaying(type?: string): boolean {
    if (!this.currentType) return false;
    if (type) return this.currentType === type;
    return true;
  }

  public stop() {
    this.activeSourceNodes.forEach((node) => {
      if (typeof node === 'number') {
        window.clearInterval(node);
      } else if ('stop' in node && typeof (node as AudioScheduledSourceNode).stop === 'function') {
        try {
          (node as AudioScheduledSourceNode).stop();
        } catch {
          // Ignore
        }
      }
    });
    this.activeSourceNodes = [];
    this.currentType = null;
  }

  public play(type: 'alpha' | 'brown' | 'rain') {
    this.initContext();
    if (!this.ctx) return;

    this.stop();
    this.currentType = type;

    this.gainNode = this.ctx.createGain();
    this.gainNode.gain.setValueAtTime(this.volume, this.ctx.currentTime);
    this.gainNode.connect(this.ctx.destination);

    if (type === 'alpha') {
      this.playAlphaBeats();
    } else if (type === 'brown') {
      this.playBrownNoise();
    } else if (type === 'rain') {
      this.playRain();
    }
  }

  // 14Hz Alpha Wave Binaural Tone
  private playAlphaBeats() {
    if (!this.ctx || !this.gainNode) return;

    // Base carrier frequency (200Hz) and binaural target (+14Hz)
    const oscLeft = this.ctx.createOscillator();
    const oscRight = this.ctx.createOscillator();
    const merger = this.ctx.createChannelMerger(2);

    oscLeft.type = 'sine';
    oscRight.type = 'sine';
    oscLeft.frequency.setValueAtTime(196, this.ctx.currentTime);
    oscRight.frequency.setValueAtTime(210, this.ctx.currentTime); // 14 Hz difference

    const pannerLeft = this.ctx.createStereoPanner ? this.ctx.createStereoPanner() : null;
    const pannerRight = this.ctx.createStereoPanner ? this.ctx.createStereoPanner() : null;

    if (pannerLeft && pannerRight) {
      pannerLeft.pan.setValueAtTime(-1, this.ctx.currentTime);
      pannerRight.pan.setValueAtTime(1, this.ctx.currentTime);
      oscLeft.connect(pannerLeft);
      oscRight.connect(pannerRight);
      pannerLeft.connect(this.gainNode);
      pannerRight.connect(this.gainNode);
      this.activeSourceNodes.push(pannerLeft, pannerRight);
    } else {
      oscLeft.connect(merger, 0, 0);
      oscRight.connect(merger, 0, 1);
      merger.connect(this.gainNode);
      this.activeSourceNodes.push(merger);
    }

    oscLeft.start();
    oscRight.start();
    this.activeSourceNodes.push(oscLeft, oscRight);
  }

  // Brown / Deep Focus Noise (warm, deep acoustic dampening)
  private playBrownNoise() {
    if (!this.ctx || !this.gainNode) return;

    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);

    let lastOut = 0.0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      output[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = output[i];
      output[i] *= 3.5; // Gain boost
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    // Filter to soften the low frequencies
    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(450, this.ctx.currentTime);

    whiteNoise.connect(filter);
    filter.connect(this.gainNode);

    whiteNoise.start();
    this.activeSourceNodes.push(whiteNoise, filter);
  }

  // Gentle Rain Ambient Atmosphere
  private playRain() {
    if (!this.ctx || !this.gainNode) return;

    const bufferSize = this.ctx.sampleRate * 3;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);

    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      output[i] = (b0 + b1 + b2) * 0.5;
    }

    const rainSource = this.ctx.createBufferSource();
    rainSource.buffer = noiseBuffer;
    rainSource.loop = true;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(800, this.ctx.currentTime);

    rainSource.connect(filter);
    filter.connect(this.gainNode);

    rainSource.start();
    this.activeSourceNodes.push(rainSource, filter);
  }
}

export const soundEngine = new AmbientAudioEngine();
