#!/usr/bin/env python3
import wave
import struct
import math
import random

def generate_ambient_music(filename, duration=300, sample_rate=44100):
    print(f"Generating {duration}s ambient music...")
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        num_samples = int(duration * sample_rate)
        notes = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99]
        volume = 0.18
        
        for i in range(num_samples):
            t = i / sample_rate
            left = 0.0
            right = 0.0
            
            for note_idx, freq in enumerate(notes):
                detune = 1.0 + (note_idx * 0.001)
                vibrato = 1.0 + 0.05 * math.sin(2 * math.pi * 0.08 * t + note_idx)
                env1 = 0.5 + 0.5 * math.sin(2 * math.pi * 0.02 * t + note_idx * 0.3)
                env2 = 0.5 + 0.5 * math.sin(2 * math.pi * 0.03 * t + note_idx * 0.5)
                env = (env1 + env2) / 2
                
                for h in range(1, 5):
                    amplitude = volume / (h * 1.2) * env * vibrato
                    phase = 2 * math.pi * freq * detune * h * t
                    pan = 0.6 + 0.4 * math.sin(note_idx * 0.7)
                    left += amplitude * math.sin(phase)
                    right += amplitude * math.sin(phase) * pan
            
            if i % (sample_rate * 30) == 0:
                print(f"  {i//sample_rate}s / {duration}s")
            
            texture = (random.random() - 0.5) * 0.015
            left += texture
            right += texture * 0.7
            left = max(-1.0, min(1.0, left))
            right = max(-1.0, min(1.0, right))
            
            wav_file.writeframes(struct.pack('<hh', int(left * 32767), int(right * 32767)))
        
        print(f"Done: {filename}")

import os
os.makedirs("assets/music/calm", exist_ok=True)
generate_ambient_music("assets/music/calm/ambient_5min.wav", duration=300)
