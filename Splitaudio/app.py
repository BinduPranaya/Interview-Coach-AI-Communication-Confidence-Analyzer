from pydub import AudioSegment
import math
import os

def split_audio(input_file, output_folder, chunk_length_ms=10000):
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return
    
    # Load audio
    audio = AudioSegment.from_wav(input_file)
    
    # Make output folder if not exists
    os.makedirs(output_folder, exist_ok=True)

    total_length_ms = len(audio)
    num_chunks = math.ceil(total_length_ms / chunk_length_ms)

    for i in range(num_chunks):
        start = i * chunk_length_ms
        end = min(start + chunk_length_ms, total_length_ms)
        chunk = audio[start:end]

        chunk_name = f"{output_folder}/chunk_{i+1}.wav"
        chunk.export(chunk_name, format="wav")
        print(f"Saved: {chunk_name}")

    print("Done!")

# Example usage:
split_audio("silence.wav", "output_clips", chunk_length_ms=5000)  # 5 sec clips
