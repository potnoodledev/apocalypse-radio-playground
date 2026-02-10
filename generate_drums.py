import numpy as np
from scipy.io import wavfile
import os

SAMPLE_RATE = 44100
BPM = 120
BEAT_DURATION = 60.0 / BPM  # 0.5 seconds per beat

def generate_kick(duration=0.15, sample_rate=SAMPLE_RATE):
    """Low frequency sine sweep 150Hz->50Hz with fast decay."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Frequency sweep from 150 to 50 Hz
    freq = 150 * np.exp(-t * np.log(150/50) / duration)
    # Phase is integral of frequency
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    # Amplitude envelope - fast exponential decay
    envelope = np.exp(-t * 30)
    kick = np.sin(phase) * envelope
    # Add a click at the start for attack
    click_len = int(0.005 * sample_rate)
    click = np.zeros_like(kick)
    click[:click_len] = np.sin(2 * np.pi * 1000 * t[:click_len]) * np.exp(-t[:click_len] * 200)
    kick = kick * 0.85 + click * 0.15
    return kick

def generate_snare(duration=0.12, sample_rate=SAMPLE_RATE):
    """White noise burst with tonal component, fast decay."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Noise component
    noise = np.random.randn(len(t))
    noise_env = np.exp(-t * 40)
    # Tonal component (around 200Hz)
    tone = np.sin(2 * np.pi * 200 * t) * np.exp(-t * 50)
    snare = noise * noise_env * 0.6 + tone * 0.4
    return snare

def generate_hihat_closed(duration=0.04, sample_rate=SAMPLE_RATE):
    """High-frequency filtered noise, very short decay."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    noise = np.random.randn(len(t))
    # High-pass effect: differentiate the noise
    hp_noise = np.diff(noise, prepend=0)
    envelope = np.exp(-t * 100)
    hihat = hp_noise * envelope
    return hihat

def generate_hihat_open(duration=0.12, sample_rate=SAMPLE_RATE):
    """High-frequency filtered noise, longer decay."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    noise = np.random.randn(len(t))
    hp_noise = np.diff(noise, prepend=0)
    envelope = np.exp(-t * 20)
    hihat = hp_noise * envelope
    return hihat

def place_sound(track, sound, position_samples, volume=1.0):
    """Place a sound into the track at a given sample position."""
    start = int(position_samples)
    end = start + len(sound)
    if end > len(track):
        end = len(track)
        sound = sound[:end - start]
    track[start:end] += sound * volume

def beat_to_samples(beat):
    """Convert beat number to sample position."""
    return int(beat * BEAT_DURATION * SAMPLE_RATE)

def normalize_and_convert(track):
    """Normalize to 16-bit range."""
    if np.max(np.abs(track)) > 0:
        track = track / np.max(np.abs(track)) * 0.9
    return (track * 32767).astype(np.int16)

def generate_intro(num_beats=16):
    """Light hi-hats only, building atmosphere. 16 beats = 8 seconds."""
    total_samples = int(num_beats * BEAT_DURATION * SAMPLE_RATE)
    track = np.zeros(total_samples)

    # Hi-hats on eighth notes (every 0.5 beat), gradually getting louder
    total_eighth_notes = num_beats * 2
    for i in range(total_eighth_notes):
        beat_pos = i * 0.5
        # Volume builds from 0.15 to 0.6 over the intro
        vol = 0.15 + 0.45 * (i / total_eighth_notes)
        # Alternate between closed hi-hats, occasional open on beat
        if i % 4 == 0 and i > total_eighth_notes // 2:
            place_sound(track, generate_hihat_open(), beat_to_samples(beat_pos), vol)
        else:
            place_sound(track, generate_hihat_closed(), beat_to_samples(beat_pos), vol)

    return normalize_and_convert(track)

def generate_verse(num_beats=32):
    """Classic electronic beat: kick on 1&3, snare on 2&4, hi-hats on 8ths. 32 beats = 16 sec."""
    total_samples = int(num_beats * BEAT_DURATION * SAMPLE_RATE)
    track = np.zeros(total_samples)

    for bar in range(num_beats // 4):
        bar_offset = bar * 4
        # Kick on beats 1 and 3
        place_sound(track, generate_kick(), beat_to_samples(bar_offset + 0), 0.9)
        place_sound(track, generate_kick(), beat_to_samples(bar_offset + 2), 0.85)
        # Snare on beats 2 and 4
        place_sound(track, generate_snare(), beat_to_samples(bar_offset + 1), 0.75)
        place_sound(track, generate_snare(), beat_to_samples(bar_offset + 3), 0.75)
        # Hi-hats on eighth notes
        for eighth in range(8):
            beat_pos = bar_offset + eighth * 0.5
            place_sound(track, generate_hihat_closed(), beat_to_samples(beat_pos), 0.45)

    return normalize_and_convert(track)

def generate_chorus(num_beats=32):
    """Energetic driving pattern with fills, kick on every beat, open hats. 32 beats = 16 sec."""
    total_samples = int(num_beats * BEAT_DURATION * SAMPLE_RATE)
    track = np.zeros(total_samples)

    for bar in range(num_beats // 4):
        bar_offset = bar * 4
        # Kick on every beat (four-on-the-floor)
        for beat in range(4):
            place_sound(track, generate_kick(), beat_to_samples(bar_offset + beat), 0.95)
        # Snare on 2 and 4
        place_sound(track, generate_snare(), beat_to_samples(bar_offset + 1), 0.85)
        place_sound(track, generate_snare(), beat_to_samples(bar_offset + 3), 0.85)
        # Open hi-hats on off-beats, closed on beats
        for eighth in range(8):
            beat_pos = bar_offset + eighth * 0.5
            if eighth % 2 == 1:  # Off-beats get open hats
                place_sound(track, generate_hihat_open(), beat_to_samples(beat_pos), 0.55)
            else:
                place_sound(track, generate_hihat_closed(), beat_to_samples(beat_pos), 0.5)

        # Add a fill on every 4th bar (snare rolls on last beat)
        if (bar + 1) % 4 == 0:
            for sixteenth in range(4):
                fill_pos = bar_offset + 3 + sixteenth * 0.25
                place_sound(track, generate_snare(), beat_to_samples(fill_pos), 0.7 + sixteenth * 0.05)

    return normalize_and_convert(track)

def generate_outro(num_beats=16):
    """Gradually fading pattern. 16 beats = 8 seconds."""
    total_samples = int(num_beats * BEAT_DURATION * SAMPLE_RATE)
    track = np.zeros(total_samples)

    for bar in range(num_beats // 4):
        bar_offset = bar * 4
        # Fade factor: goes from 1.0 to ~0.1
        fade = 1.0 - (bar / (num_beats // 4)) * 0.85

        # Kick on 1 and 3 (fading)
        place_sound(track, generate_kick(), beat_to_samples(bar_offset + 0), 0.9 * fade)
        if bar < 3:  # Drop kick on 3 in last bar
            place_sound(track, generate_kick(), beat_to_samples(bar_offset + 2), 0.8 * fade)
        # Snare on 2 and 4 (fading, drop snare on 4 in last 2 bars)
        place_sound(track, generate_snare(), beat_to_samples(bar_offset + 1), 0.7 * fade)
        if bar < 2:
            place_sound(track, generate_snare(), beat_to_samples(bar_offset + 3), 0.7 * fade)
        # Hi-hats on eighth notes (fading)
        for eighth in range(8):
            beat_pos = bar_offset + eighth * 0.5
            hh_fade = fade * (1.0 - (eighth / 8) * 0.3)
            place_sound(track, generate_hihat_closed(), beat_to_samples(beat_pos), 0.4 * hh_fade)

    return normalize_and_convert(track)

if __name__ == "__main__":
    output_dir = r"C:\pot\apocalypse-radio-playground"

    print("Generating intro drums...")
    intro = generate_intro()
    wavfile.write(os.path.join(output_dir, "drums_intro.wav"), SAMPLE_RATE, intro)
    print(f"  -> drums_intro.wav ({len(intro)} samples, {len(intro)/SAMPLE_RATE:.1f}s)")

    print("Generating verse drums...")
    verse = generate_verse()
    wavfile.write(os.path.join(output_dir, "drums_verse.wav"), SAMPLE_RATE, verse)
    print(f"  -> drums_verse.wav ({len(verse)} samples, {len(verse)/SAMPLE_RATE:.1f}s)")

    print("Generating chorus drums...")
    chorus = generate_chorus()
    wavfile.write(os.path.join(output_dir, "drums_chorus.wav"), SAMPLE_RATE, chorus)
    print(f"  -> drums_chorus.wav ({len(chorus)} samples, {len(chorus)/SAMPLE_RATE:.1f}s)")

    print("Generating outro drums...")
    outro = generate_outro()
    wavfile.write(os.path.join(output_dir, "drums_outro.wav"), SAMPLE_RATE, outro)
    print(f"  -> drums_outro.wav ({len(outro)} samples, {len(outro)/SAMPLE_RATE:.1f}s)")

    print("\nAll drum tracks generated successfully!")
