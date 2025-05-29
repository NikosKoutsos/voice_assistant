import pvporcupine
import pyaudio
import struct
import time


access_key = "2hs/UmBDGlm0oCWqGVFzavxI6Manb3VZtiWoJ/0J1U/qargkzDHs6A=="

def test_porcupine():
    keywords = ["hey siri", "jarvis", "computer"]
    
    try:
        porcupine = pvporcupine.create(keywords=keywords, access_key=access_key)
        pa = pyaudio.PyAudio()
        
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )
        print(f"Listening for keywords: {keywords}")
        print("Press Ctrl+C to stop.")
        
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            keyword_index = porcupine.process(pcm)
            
            if keyword_index >= 0:
                detected_keyword = keywords[keyword_index]
                print(f"Detected keyword: {detected_keyword}")
                print("Assistant activated!")
                time.sleep(1)  # Simulate some processing time
                
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        if 'porcupine' in locals():
            porcupine.delete()
        if 'audio_stream' in locals():
            audio_stream.stop_stream()
        if 'pa' in locals():
            pa.terminate()
            
if __name__ == "__main__":
    test_porcupine()