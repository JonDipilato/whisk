#!/usr/bin/env python3
"""Generate a simple ambient music track for testing."""
import wave
import struct
import math
import random

def generate_ambient_music(filename, duration=120, sample_rate=44100):
    """Generate a simple ambient music track."""
    print(f"Generating {duration}s ambient music...")
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        num_samples = int(duration * sample_rate)
        
        # Ambient pad parameters
        notes = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
        volume = 0.15
        
        for i in range(num_samples):
            t = i / sample_rate
            
            # Create ambient pad with multiple oscillators
            left = 0.0
            right = 0.0
            
            for note_idx, freq in enumerate(notes):
                # Slight detune for richness
                detune = 1.0 + (note_idx * 0.002)
                
                # Slow amplitude modulation for ambient feel
                vibrato = 1.0 + 0.1 * math.sin(2 * math.pi * 0.1 * t + note_idx)
                
                # Very slow attack/release envelope
                env = 0.5 + 0.5 * math.sin(2 * math.pi * 0.05 * t + note_idx * 0.5)
                env = env * env
                
                # Add some harmonics
                for h in range(1, 4):
                    amplitude = volume / h * env * vibrato
                    phase = 2 * math.pi * freq * detune * h * t
                    
                    # Stereo spread
                    pan = 0.7 + 0.3 * math.sin(note_idx)
                    left += amplitude * math.sin(phase)
                    right += amplitude * math.sin(phase) * pan
            
            # Add subtle noise for texture
            noise = (random.random() - 0.5) * 0.02
            left += noise
            right += noise * 0.8
            
            # Soft clipping
            left = max(-1.0, min(1.0, left))
            right = max(-1.0, min(1.0, right))
            
            # Convert to 16-bit integer
            left_int = int(left * 32767)
            right_int = int(right * 32767)
            
            # Pack as little-endian
            wav_file.writeframes(struct.pack('<hh', left_int, right_int))
            
            # Progress indicator
            if i % sample_rate == 0:
                print(f"  {i//sample_rate}s / {duration}s", end='\r')
        
        print(f"\nGenerated: {filename}")

if __name__ == "__main__":
    import os
    os.makedirs("assets/music/calm", exist_ok=True)
    generate_ambient_music("assets/music/calm/ambient_bedtime.wav", duration=180)
    print("Done!")
