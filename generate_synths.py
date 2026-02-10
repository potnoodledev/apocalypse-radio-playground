import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import os

SAMPLE_RATE = 44100
BPM = 120
BEAT_DUR = 60.0 / BPM  # 0.5 seconds per beat

# C minor scale frequencies
C4 = 261.63
D4 = 293.66
Eb4 = 311.13
F4 = 349.23
G4 = 392.00
Ab4 = 415.30
Bb4 = 466.16
C5 = 523.25
Eb5 = 622.25
G5 = 783.99
Ab3 = 207.65
Eb3 = 155.56
Bb3 = 233.08


def lowpass_filter(signal, cutoff, sr=SAMPLE_RATE, order=4):
    nyq = 0.5 * sr
    norm_cutoff = min(cutoff / nyq, 0.99)
    b, a = butter(order, norm_cutoff, btype='low')
    return lfilter(b, a, signal)


def adsr_envelope(num_samples, attack=0.01, decay=0.1, sustain_level=0.7, release=0.1, sr=SAMPLE_RATE):
    """Generate ADSR envelope."""
    env = np.zeros(num_samples)
    a_samples = int(attack * sr)
    d_samples = int(decay * sr)
    r_samples = int(release * sr)
    s_samples = max(0, num_samples - a_samples - d_samples - r_samples)

    idx = 0
    # Attack
    if a_samples > 0:
        end = min(idx + a_samples, num_samples)
        env[idx:end] = np.linspace(0, 1, end - idx)
        idx = end
    # Decay
    if idx < num_samples and d_samples > 0:
        end = min(idx + d_samples, num_samples)
        env[idx:end] = np.linspace(1, sustain_level, end - idx)
        idx = end
    # Sustain
    if idx < num_samples and s_samples > 0:
        end = min(idx + s_samples, num_samples)
        env[idx:end] = sustain_level
        idx = end
    # Release
    if idx < num_samples:
        env[idx:] = np.linspace(sustain_level, 0, num_samples - idx)

    return env


def saw_wave(freq, duration, sr=SAMPLE_RATE):
    t = np.arange(int(duration * sr)) / sr
    return 2.0 * (t * freq % 1.0) - 1.0


def square_wave(freq, duration, sr=SAMPLE_RATE):
    t = np.arange(int(duration * sr)) / sr
    return np.sign(np.sin(2 * np.pi * freq * t))


def detuned_saw_pad(freqs, duration, detune_hz=3.0, sr=SAMPLE_RATE):
    """Multiple detuned saw oscillators for pad sound."""
    n = int(duration * sr)
    signal = np.zeros(n)
    for f in freqs:
        for offset in [-detune_hz, 0, detune_hz]:
            signal += saw_wave(f + offset, duration, sr)
    # Normalize by number of oscillators
    signal /= (len(freqs) * 3)
    return signal


def save_wav(filename, audio, sr=SAMPLE_RATE):
    # Normalize to 0.7 peak
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio * (0.7 / peak)
    # Convert to 16-bit
    audio_16 = np.int16(audio * 32767)
    wavfile.write(filename, sr, audio_16)
    print(f"Saved {filename} ({len(audio_16)} samples, {len(audio_16)/sr:.2f}s)")


# ============================================================
# SECTION 1: INTRO - Atmospheric Pad (16 beats = 8 seconds)
# ============================================================
def generate_intro():
    duration = 16 * BEAT_DUR  # 8 seconds
    n = int(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE

    # Cm chord pad: C4 + Eb4 + G4 with 3 detuned oscillators each
    pad = detuned_saw_pad([C4, Eb4, G4], duration, detune_hz=3.0)

    # Slow attack envelope (2 sec attack)
    env = adsr_envelope(n, attack=2.0, decay=0.5, sustain_level=0.8, release=2.0)
    pad *= env

    # Slow LFO on filter cutoff for movement (0.2 Hz)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)
    # Filter cutoff sweeps between 800 and 2500 Hz
    # Apply filter in chunks to simulate moving cutoff
    chunk_size = SAMPLE_RATE // 10  # 100ms chunks
    filtered = np.zeros(n)
    for i in range(0, n, chunk_size):
        end = min(i + chunk_size, n)
        chunk = pad[i:end]
        mid = (i + end) // 2
        if mid < n:
            cutoff = 800 + 1700 * lfo[min(mid, n - 1)]
        else:
            cutoff = 800
        filtered[i:end] = lowpass_filter(np.concatenate([pad[max(0, i - 1000):i], chunk]),
                                          cutoff)[-(end - i):]

    save_wav("synth_intro.wav", filtered)
    return filtered


# ============================================================
# SECTION 2: VERSE - Arpeggiated Synth (32 beats = 16 seconds)
# ============================================================
def generate_verse():
    duration = 32 * BEAT_DUR  # 16 seconds
    n = int(duration * SAMPLE_RATE)

    # Arp pattern: C4-Eb4-G4-C5 at 8th note speed (each note = half a beat)
    arp_notes = [C4, Eb4, G4, C5]
    eighth_dur = BEAT_DUR / 2  # 0.25 seconds
    num_eighths = int(duration / eighth_dur)

    signal = np.zeros(n)
    for i in range(num_eighths):
        note_freq = arp_notes[i % len(arp_notes)]
        start = int(i * eighth_dur * SAMPLE_RATE)
        end = min(int((i + 1) * eighth_dur * SAMPLE_RATE), n)
        note_len = end - start

        # Single saw wave with plucky envelope
        note = saw_wave(note_freq, note_len / SAMPLE_RATE)
        env = adsr_envelope(note_len, attack=0.005, decay=0.1, sustain_level=0.3, release=0.05)
        note *= env

        signal[start:end] += note[:end - start]

    # Bright filter at 3kHz
    signal = lowpass_filter(signal, 3000)

    save_wav("synth_verse.wav", signal)
    return signal


# ============================================================
# SECTION 3: CHORUS - Chord Stabs + Lead Melody (32 beats = 16 sec)
# ============================================================
def generate_chorus():
    duration = 32 * BEAT_DUR  # 16 seconds
    n = int(duration * SAMPLE_RATE)

    # Chord progression: Cm - Ab - Eb - Bb, 2 beats each, repeating
    chords = [
        [C4, Eb4, G4],          # Cm
        [Ab3, C4, Eb4],         # Ab
        [Eb3, G4, Bb4],         # Eb (using Eb3 root with G4 and Bb4)
        [Bb3, D4, F4],          # Bb
    ]
    chord_dur = 2 * BEAT_DUR  # 1 second per chord
    num_chords = int(duration / chord_dur)

    stabs = np.zeros(n)
    for i in range(num_chords):
        chord = chords[i % len(chords)]
        start = int(i * chord_dur * SAMPLE_RATE)
        end = min(int((i + 1) * chord_dur * SAMPLE_RATE), n)
        chord_len = end - start

        # Saw waves for chord stab
        chord_signal = np.zeros(chord_len)
        for freq in chord:
            chord_signal += saw_wave(freq, chord_len / SAMPLE_RATE)
        chord_signal /= len(chord)

        # Medium attack envelope for stabs
        env = adsr_envelope(chord_len, attack=0.05, decay=0.15, sustain_level=0.7, release=0.1)
        chord_signal *= env

        stabs[start:end] += chord_signal[:end - start]

    stabs = lowpass_filter(stabs, 2500)

    # Lead melody: Bb4-C5-Eb5-G4 motif, each note = 2 beats, repeating
    lead_notes = [Bb4, C5, Eb5, G4]
    lead_dur = 2 * BEAT_DUR  # 1 second per note
    num_lead = int(duration / lead_dur)

    lead = np.zeros(n)
    for i in range(num_lead):
        note_freq = lead_notes[i % len(lead_notes)]
        start = int(i * lead_dur * SAMPLE_RATE)
        end = min(int((i + 1) * lead_dur * SAMPLE_RATE), n)
        note_len = end - start

        t_note = np.arange(note_len) / SAMPLE_RATE
        # Square wave with vibrato (5Hz LFO, ±10 cents)
        vibrato = note_freq * (2 ** (0.1 / 12 * np.sin(2 * np.pi * 5 * t_note)))
        phase = np.cumsum(vibrato / SAMPLE_RATE)
        note_signal = np.sign(np.sin(2 * np.pi * phase))

        env = adsr_envelope(note_len, attack=0.02, decay=0.1, sustain_level=0.6, release=0.15)
        note_signal *= env

        lead[start:end] += note_signal[:end - start]

    lead = lowpass_filter(lead, 4000)

    # Mix: stabs at 0.6, lead at 0.4
    combined = stabs * 0.6 + lead * 0.4

    save_wav("synth_chorus.wav", combined)
    return combined


# ============================================================
# SECTION 4: OUTRO - Atmospheric Pad Fading Out (16 beats = 8 sec)
# ============================================================
def generate_outro():
    duration = 16 * BEAT_DUR  # 8 seconds
    n = int(duration * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE

    # Same Cm pad as intro
    pad = detuned_saw_pad([C4, Eb4, G4], duration, detune_hz=3.0)

    # Envelope: moderate attack, long fade to silence
    env = adsr_envelope(n, attack=0.5, decay=0.5, sustain_level=0.7, release=5.0)
    # Additional linear fade-out over entire duration
    fade = np.linspace(1.0, 0.0, n)
    pad *= env * fade

    # LFO filter sweep
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t)
    chunk_size = SAMPLE_RATE // 10
    filtered = np.zeros(n)
    for i in range(0, n, chunk_size):
        end = min(i + chunk_size, n)
        chunk = pad[i:end]
        mid = (i + end) // 2
        cutoff = 600 + 1400 * lfo[min(mid, n - 1)]
        filtered[i:end] = lowpass_filter(np.concatenate([pad[max(0, i - 1000):i], chunk]),
                                          cutoff)[-(end - i):]

    save_wav("synth_outro.wav", filtered)
    return filtered


if __name__ == "__main__":
    os.chdir(r"C:\pot\apocalypse-radio-playground")
    print("Generating synth tracks...")
    print("\n--- INTRO ---")
    generate_intro()
    print("\n--- VERSE ---")
    generate_verse()
    print("\n--- CHORUS ---")
    generate_chorus()
    print("\n--- OUTRO ---")
    generate_outro()
    print("\nAll synth tracks generated!")
