import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import os

SAMPLE_RATE = 44100
BPM = 120
BEAT_DUR = 60.0 / BPM  # 0.5 seconds per beat

# C minor scale bass frequencies
NOTES = {
    'C2': 65.41,
    'D2': 73.42,
    'Eb2': 77.78,
    'F2': 87.31,
    'G2': 98.00,
    'Ab2': 103.83,
    'Bb2': 116.54,
    'C3': 130.81,
}


def sawtooth_wave(freq, duration, sample_rate=SAMPLE_RATE):
    """Generate a sawtooth waveform."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Sawtooth: rises from -1 to 1 over each period
    wave = 2.0 * (t * freq - np.floor(0.5 + t * freq))
    return t, wave


def low_pass_filter(signal, cutoff, sample_rate=SAMPLE_RATE, order=4):
    """Apply a Butterworth low-pass filter."""
    nyq = sample_rate / 2.0
    normalized_cutoff = min(cutoff / nyq, 0.99)
    b, a = butter(order, normalized_cutoff, btype='low')
    return lfilter(b, a, signal)


def adsr_envelope(num_samples, attack=0.01, decay=0.05, sustain_level=0.7, release=0.1, sample_rate=SAMPLE_RATE):
    """Generate an ADSR envelope."""
    env = np.zeros(num_samples)
    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    sustain_samples = num_samples - attack_samples - decay_samples - release_samples

    if sustain_samples < 0:
        # Short note: just do attack and release
        half = num_samples // 2
        env[:half] = np.linspace(0, 1, half)
        env[half:] = np.linspace(1, 0, num_samples - half)
        return env

    idx = 0
    # Attack
    env[idx:idx + attack_samples] = np.linspace(0, 1, attack_samples)
    idx += attack_samples
    # Decay
    env[idx:idx + decay_samples] = np.linspace(1, sustain_level, decay_samples)
    idx += decay_samples
    # Sustain
    env[idx:idx + sustain_samples] = sustain_level
    idx += sustain_samples
    # Release
    env[idx:idx + release_samples] = np.linspace(sustain_level, 0, release_samples)
    return env


def make_bass_note(freq, duration, cutoff=600, volume=0.8):
    """Create a single bass note with saw wave, filter, and envelope."""
    t, wave = sawtooth_wave(freq, duration)
    # Add a sub-oscillator (sine wave one octave below) for thickness
    wave = wave * 0.7 + 0.3 * np.sin(2 * np.pi * (freq / 2) * t)
    # Low-pass filter
    wave = low_pass_filter(wave, cutoff)
    # ADSR envelope
    env = adsr_envelope(len(wave))
    wave = wave * env
    # Normalize
    wave = wave / (np.max(np.abs(wave)) + 1e-9) * volume
    return wave


def save_wav(filename, audio, sample_rate=SAMPLE_RATE):
    """Save audio as 16-bit WAV."""
    # Clip and convert to int16
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)
    wavfile.write(filename, sample_rate, audio_int16)
    print(f"Saved {filename} ({len(audio_int16)} samples, {len(audio_int16)/sample_rate:.2f}s)")


# ============================================================
# SECTION 1: INTRO - 16 beats (8 sec)
# Very subtle sub bass, low C2 drone barely audible
# ============================================================
def generate_intro():
    duration = 16 * BEAT_DUR  # 8 seconds
    num_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # Pure sine sub bass at C2 - very subtle
    wave = np.sin(2 * np.pi * NOTES['C2'] * t)
    # Very gentle filter
    wave = low_pass_filter(wave, 200)
    # Slow fade in over first 2 seconds, then sustain
    envelope = np.ones(num_samples)
    fade_in_samples = int(2.0 * SAMPLE_RATE)
    envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)
    # Gentle fade out at the end
    fade_out_samples = int(1.0 * SAMPLE_RATE)
    envelope[-fade_out_samples:] = np.linspace(1, 0.8, fade_out_samples)

    wave = wave * envelope * 0.25  # Very quiet
    save_wav("bass_intro.wav", wave)


# ============================================================
# SECTION 2: VERSE - 32 beats (16 sec)
# Driving synthwave bass: C2-C2-Eb2-F2 pattern repeating
# Each note is 8th note length with portamento feel
# ============================================================
def generate_verse():
    pattern = ['C2', 'C2', 'Eb2', 'F2']
    note_duration = BEAT_DUR  # Each note is one beat
    total_beats = 32
    repeats = total_beats // len(pattern)

    all_notes = []
    for _ in range(repeats):
        for note_name in pattern:
            freq = NOTES[note_name]
            note = make_bass_note(freq, note_duration, cutoff=500, volume=0.8)
            all_notes.append(note)

    audio = np.concatenate(all_notes)

    # Add slight portamento by smoothing transitions
    # Apply overall slight compression/warmth
    audio = low_pass_filter(audio, 800)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.8

    save_wav("bass_verse.wav", audio)


# ============================================================
# SECTION 3: CHORUS - 32 beats (16 sec)
# Arpeggio: C2-G2-Ab2-F2-Eb2-F2-G2-C3
# Full saw bass with filter sweep
# ============================================================
def generate_chorus():
    pattern = ['C2', 'G2', 'Ab2', 'F2', 'Eb2', 'F2', 'G2', 'C3']
    note_duration = BEAT_DUR  # One beat per note
    total_beats = 32
    repeats = total_beats // len(pattern)

    all_notes = []
    note_index = 0
    total_notes = total_beats

    for rep in range(repeats):
        for i, note_name in enumerate(pattern):
            freq = NOTES[note_name]
            # Filter sweep: cutoff increases through each repetition
            progress = (rep * len(pattern) + i) / total_notes
            cutoff = 400 + progress * 500  # 400Hz to 900Hz sweep
            note = make_bass_note(freq, note_duration, cutoff=cutoff, volume=0.85)
            all_notes.append(note)

    audio = np.concatenate(all_notes)
    audio = audio / (np.max(np.abs(audio)) + 1e-9) * 0.85

    save_wav("bass_chorus.wav", audio)


# ============================================================
# SECTION 4: OUTRO - 16 beats (8 sec)
# Sustained C2 with slow fade out
# ============================================================
def generate_outro():
    duration = 16 * BEAT_DUR  # 8 seconds
    num_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    # Saw wave at C2
    wave = 2.0 * (t * NOTES['C2'] - np.floor(0.5 + t * NOTES['C2']))
    # Add sub sine
    wave = wave * 0.6 + 0.4 * np.sin(2 * np.pi * NOTES['C2'] * t)
    # Filter
    wave = low_pass_filter(wave, 500)

    # Long fade out over entire duration
    fade_envelope = np.linspace(0.8, 0.0, num_samples)
    wave = wave * fade_envelope
    wave = wave / (np.max(np.abs(wave)) + 1e-9) * 0.7

    save_wav("bass_outro.wav", wave)


# ============================================================
# Generate all sections
# ============================================================
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Generating bass tracks for Wasteland Frequencies...")
    print(f"Tempo: {BPM} BPM, Key: C minor\n")

    generate_intro()
    generate_verse()
    generate_chorus()
    generate_outro()

    print("\nAll bass tracks generated!")
