import pvporcupine
import pyaudio
import struct
from colorama import init, Fore, Style

class WakeWordDetector:
    def __init__(self, access_key, wake_words=None, sensitivity=0.5):
        """Initialize the wake word detector"""
        self.access_key = access_key
        self.wake_words = wake_words or ["hey google", "jarvis", "computer"]
        self.sensitivity = sensitivity
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
    
    def start(self):
        """Start the wake word detection"""
        
        #Initialize porcupine with specified wake words
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=self.wake_words,
                sensitivities=[self.sensitivity] * len(self.wake_words)
            )
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print(f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}Wake word detection has started.{Style.RESET_ALL} {Style.DIM}{Fore.LIGHTRED_EX}Listening for{Style.RESET_ALL} {Fore.RED}{self.wake_words} {Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"Error initializing wake word detection: {e}")
            self.cleanup()
            return False
    
    def listen(self):
        """Listen for wake words"""
        try:
            #Read audio from microphone
            pcm = self.audio_stream.read(self.porcupine.frame_length)
            #Convert audio to required format
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            # Process audio frame
            keyword_index = self.porcupine.process(pcm)
            
            #If wake words detected
            if keyword_index >= 0:
                detected_keyword = self.wake_words[keyword_index]
                return detected_keyword
            return None
        except Exception as e:
            print(f"Error in listening for wake words: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.audio_stream:
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.pa:
            self.pa.terminate()
            self.pa = None
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None