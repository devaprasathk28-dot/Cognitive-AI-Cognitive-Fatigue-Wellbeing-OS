import os
import wave
import math
import struct
import random
import tempfile
import threading

try:
    import winsound
except ImportError:
    winsound = None

_CURRENT_SOUND = None
_TEMP_FILES = []


def _generate_binaural_wave(filename: str, duration_sec: int = 10, base_freq: float = 216.0, beat_freq: float = 40.0):
    """Generates a soft, ambient binaural flow state wave file."""
    sample_rate = 22050
    num_samples = sample_rate * duration_sec
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(2)  # Stereo for binaural beat
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        freq_l = base_freq
        freq_r = base_freq + beat_freq
        
        frames = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            # Smooth envelope at loop seams
            fade = min(1.0, min(t / 0.5, (duration_sec - t) / 0.5))
            
            sample_l = int(1800 * fade * math.sin(2 * math.pi * freq_l * t))
            sample_r = int(1800 * fade * math.sin(2 * math.pi * freq_r * t))
            
            # Subtle low-frequency modulation
            mod = 0.8 + 0.2 * math.sin(2 * math.pi * 0.2 * t)
            sample_l = int(sample_l * mod)
            sample_r = int(sample_r * mod)
            
            frames += struct.pack('<hh', sample_l, sample_r)
        
        wav.writeframes(frames)


def _generate_rain_noise(filename: str, duration_sec: int = 10):
    """Generates a soft, soothing low-pass filtered rain/ambient noise file."""
    sample_rate = 22050
    num_samples = sample_rate * duration_sec
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        frames = bytearray()
        last = 0.0
        for i in range(num_samples):
            t = i / sample_rate
            fade = min(1.0, min(t / 0.5, (duration_sec - t) / 0.5))
            
            # Low-pass filter (brown noise approximation)
            white = random.uniform(-1.0, 1.0)
            brown = (last + (0.04 * white)) / 1.04
            last = brown
            
            val = int(brown * 3800 * fade)
            val = max(-32767, min(32767, val))
            frames += struct.pack('<h', val)
            
        wav.writeframes(frames)


def play_ambient(sound_type: str):
    """Plays looping ambient soundscapes ('binaural', 'rain', 'silence')."""
    global _CURRENT_SOUND
    if not winsound:
        return

    stop_ambient()
    if sound_type == "silence" or not sound_type:
        return

    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        _TEMP_FILES.append(tmp.name)

        if sound_type == "binaural":
            _generate_binaural_wave(tmp.name, duration_sec=8, base_freq=180.0, beat_freq=14.0)  # Alpha/Theta wave
        elif sound_type == "rain":
            _generate_rain_noise(tmp.name, duration_sec=8)
        else:
            return

        winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        _CURRENT_SOUND = sound_type
    except Exception as e:
        print(f"[AmbientAudio] Play error: {e}")


def stop_ambient():
    """Stops any currently playing ambient soundscape."""
    global _CURRENT_SOUND
    if not winsound:
        return
    try:
        winsound.PlaySound(None, 0)
        _CURRENT_SOUND = None
    except Exception:
        pass


def cleanup_temp_audio():
    stop_ambient()
    for f in _TEMP_FILES:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
