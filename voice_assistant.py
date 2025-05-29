import os
import sys
import re
import time
import speech_recognition as sr
import pyttsx3
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access API keys
astronomy_api_id = os.getenv("ASTRONOMY_API_ID")
astronomy_api_secret = os.getenv("ASTRONOMY_API_SECRET")
weather_api_key = os.getenv("WEATHER_API_KEY")
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

#Access Wake Word
access_key = os.getenv("WAKE_WORD_ACCESS_KEY")

# Import project modules
from utils.wake_word_detector import WakeWordDetector
from skills.spotify_skill import SpotifySkill
from skills.weather_skill import WeatherSkill
from skills.web_skill import WebSkill
from skills.moonphase_skill import MoonPhaseSkill
from utils.common import TimeUtility, SystemUtility

init(autoreset=False)

class VoiceAssistant:
    """Main voice assistant class that coordinates all functionality"""
    def __init__(self, config=None):
        """Initialize the voice assistant with configuration"""
        # Default config if none provided
        self.config = config or {
            "wake_word": {
                "access_key": access_key,
                "wake_words": ["jarvis", "computer", "hey google"],
                "sensitivity": 0.7
            },
            "api_keys": {
                "openai": "sk-proj-YOUR_OPENAI_API_KEY",
                "weather": weather_api_key,
                "astronomy" : {
                    "app_id": astronomy_api_id,
                    "app_secret": astronomy_api_secret
                }
            },
            "spotify": {
                "client_id": spotify_client_id,
                "client_secret": spotify_client_secret,
                "redirect_uri": "http://localhost:8888/callback"
            }
        }
        
        self.moon_phase_skill = MoonPhaseSkill(api_key=self.config["api_keys"]["astronomy"])
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200  # Adjust for microphone sensitivity
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Configure voice
        voices = self.engine.getProperty('voices')
        # Try to find a female voice (often provides better clarity)
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate
        self.engine.setProperty('rate', 180)  # Speed of speech (words per minute)
        
        # State variables
        self.is_listening = False
        self.is_active = True
        
        # Initialize skills
        self.init_skills()
        
        # Initialize command mapping
        self.init_commands()
    
    def init_skills(self):
        """Initialize all skill modules"""
        # Weather skill
        self.weather_skill = WeatherSkill(self.config["api_keys"]["weather"])
        
        # Spotify skill
        self.spotify_skill = SpotifySkill(
            self.config["spotify"]["client_id"],
            self.config["spotify"]["client_secret"],
            self.config["spotify"]["redirect_uri"]
        )
        
        # Web skill (static methods, no initialization needed)
        self.web_skill = WebSkill
        
        # Time utility (static methods, no initialization needed)
        self.time_utility = TimeUtility
        
        # System utility (static methods, no initialization needed)
        self.system_utility = SystemUtility
    
    def init_commands(self):
        """Initialize command mapping - maps user phrases to functions"""
        self.commands = {
            # Weather commands
            r"weather(?: in| for)? (.+)": lambda match: self.handle_weather(match),
            r"weather": lambda: self.handle_weather("current location"),
            r"forecast(?: in| for)? (.+)": lambda match: self.handle_forecast(match),
            r"forecast": lambda: self.handle_forecast("current location"),
            
            # Moon phase commands
            r"(what is the |what's the |current |)moon phase": self.handle_moon_phase,
            r"how is the moon( today| tonight| looking|)": self.handle_moon_phase,
            r"when('s| is) the next full moon": self.handle_next_full_moon,
            r"(when will|when can) I (see|expect) the next full moon": self.handle_next_full_moon,
            
            # System commands
            r"(internet |connection |)(speed test|test speed)": self.handle_speedtest,
            r"find (?:my )?(phone|mobile)": self.handle_find_phone,
            r"locate (?:my )?(phone|mobile)": self.handle_find_phone,
            r"where(?:'s| is) my (phone|mobile)": self.handle_find_phone,
            r"ring (?:my )?(phone|mobile)": self.handle_find_phone,
            
            # Time and date commands
            r"time": self.handle_time,
            r"date|day|today": self.handle_date,
            
            # Web search and information commands
            r"(?:tell me|what is|who is|who was|what are|lookup|wikipedia) (?:about |for )?(.*?)(?:\?)?$": self.handle_wikipedia,
            r"search for (.+)": self.handle_web_search,
            r"open (?!website|site|page|url)(.+)": self.handle_open_app,
            r"go to (.+)": self.handle_open_website,
            r"(youtube\.com|youtube|gmail\.com|gmail|google\.com|facebook\.com|twitter\.com|reddit\.com|netflix\.com|google\.com|claude\.ai|crunchyroll\.com|crunchyroll)": self.handle_open_website,
            
            # Spotify commands
            r"play (?:the )?(liked songs|discover weekly|release radar|roulette|this is echo tides|this is d|daily mix 1|daily mix 2|daily mix 3|this is evanescence|Final Fantasy VII|my chemical romance|this is agnes obel)(?: on| in)? spotify": self.handle_spotify_playlist,
            r"play (.+?)(?: on| in)? spotify": self.handle_spotify_song,
            r"(pause|stop) (spotify|music)": self.handle_spotify_pause,
            r"resume (spotify|music)|play spotify|continue music": self.handle_spotify_resume,
            r"next (song|track)|skip (song|track)": lambda *args: self.handle_spotify_next(),
            r"previous (song|track)|go back (song|track)": lambda *args: self.handle_spotify_previous(),
            r"set (?:spotify |music )?volume (?:to )?([\d]+)(?: percent)?": self.handle_spotify_volume,
            r"volume up|increase volume": lambda: self.handle_system_volume("volume_up"),
            r"volume down|decrease volume": lambda: self.handle_system_volume("volume_down"),
            r"close spotify|quit spotify": self.handle_spotify_close,
            
            # Reminder commands
            r"remind me to (.+) at (.+)": self.handle_reminder,
            
            # Help and exit commands
            r"help|what can you do": self.show_help,
            r"exit|quit|stop|goodbye": self.exit
        }
    
    def speak(self, text, text_color=None):
        """Convert text to speech"""
        
        if text_color:
            print(f"{Style.DIM}{Fore.YELLOW}Assistant: {Style.RESET_ALL}{text_color}{text}{Style.RESET_ALL}")
        else:
            print(f"{Style.DIM}{Fore.YELLOW}Assistant: {Style.RESET_ALL}{text}")
        
        clean_text = re.sub(r'\x1b\[\d+m', '', text)
        self.engine.say(clean_text)
        self.engine.runAndWait()
        
        # print(f"Assistant: {text}")
        # self.engine.say(text)
        # self.engine.runAndWait()
    
    def listen(self, timeout=None):
        """Listen for user speech and convert to text"""
        with sr.Microphone() as source:
            # print(f"{Fore.CYAN}Listening...{Style.RESET_ALL}")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio)
                print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}You said:{Style.RESET_ALL} {Fore.YELLOW}{text}{Style.RESET_ALL}")
                return text.lower()
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                self.speak("Sorry, my speech service is down")
                return None
            except Exception as e:
                print(f"Error in listen: {e}")
                return None
    
    def process_command(self, text):
        """Process user commands based on pattern matching"""
        if not text:
            return
            
        # Check each command pattern
        for pattern, func in self.commands.items():
            matches = re.search(pattern, text, re.IGNORECASE)
            if matches:
                if len(matches.groups()) > 0:
                    # If there are capturing groups, pass them to the function
                    if len(matches.groups()) == 1:
                        return func(matches.group(1))
                    else:
                        return func(matches)
                else:
                    # No capturing groups, just call the function
                    return func()
        
        # If no command matched, respond with a default message
        # return f"{Style.DIM}{Fore.RED}I'm not sure how to help with that. Try asking for help to see what I can do.{Style.RESET_ALL}"
    # --- Moon PHase handlers --- #
    
    def handle_moon_phase(self, *args):
        """Handle Moon Phase requests"""
        self.speak("Getting the current moon phase...", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        result = self.moon_phase_skill.get_moon_phase()
        if result["success"]:
            self.speak(result["speech"])
            print(result["detailed_info"])
        else:
            self.speak(f"Sorry, I couldn't get the moon phase: {result['error']}")
            return result["error"]
    
    def handle_next_full_moon(self, *args):
        """Handle next full Moon requests"""
        self.speak("Getting the next full moon date...", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        result = self.moon_phase_skill.get_next_full_moon()
        
        if result["success"]:
            self.speak(result["speech"])
            return None
        else:
            self.speak(f"Sorry, I couldn't get the next full moon date: {result['error']}")
            return result["error"]

    
    
    # --- Weather handlers --- #
    def handle_weather(self, location):
        """Handle weather requests"""
        result = self.weather_skill.get_weather(location)
        
        if "error" in result:
            self.speak(f"Sorry, I couldn't get the weather: {result['error']}")
        else:
            self.speak(result["speech_summary"])
            print(result["detailed_info"])
        return None
    
    def handle_forecast(self, location):
        """Handle forecast requests"""
        self.speak(f"Getting weather forecast for {location}")
        result = self.weather_skill.get_weather_forecast(location)
        
        if "error" in result:
            self.speak(f"Sorry, I couldn't get the forecast: {result['error']}")
        else:
            self.speak(result["speech_intro"])
            for day_summary in result["day_summaries"]:
                self.speak(day_summary)
            print(result["detailed_info"])
        return None
    
    # --- System handlers --- #
    def handle_speedtest(self, *args):
        """Handle speed test requests"""
        self.speak("Starting the speed test, this may take a moment...", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        result = self.system_utility.run_speedtest()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["speech_text"])
        return None
    
    # --- Time handlers --- #
    def handle_time(self):
        """Handle time requests"""
        response = self.time_utility.get_time()
        self.speak(response)
        return None
    
    def handle_date(self):
        """Handle date requests"""
        response = self.time_utility.get_date()
        self.speak(response)
        return None
    
    # --- Web and information handlers --- #
    def handle_wikipedia(self, query):
        """Handle Wikipedia searches"""
        self.speak(f"Looking up information about {Style.BRIGHT}{Fore.CYAN}{query}{Style.RESET_ALL}", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        result = self.web_skill.get_wikipedia_summary(query)
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["speech_text"])
        return None
    
    def handle_web_search(self, query):
        """Handle web search requests"""
        self.speak(f"Searching the web for {Style.BRIGHT}{Fore.CYAN}{query}",f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        response = self.web_skill.search_web(query)
        if "error" in response:
            return response["error"]
        else:
            return None
    
    def handle_open_app(self, app_name):
        """Handle application opening requests"""
        response = self.web_skill.open_application(app_name)
        return response
    
    def handle_open_website(self, website_name):
        """Handle website opening requests"""
        response = self.web_skill.open_website(website_name)
        return response
    
    # --- Spotify handlers --- #
    def handle_spotify_song(self, song_name):
        """Handle playing a song on Spotify"""
        result = self.spotify_skill.play_song(song_name)
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_playlist(self, playlist_name):
        """Handle playing a playlist on Spotify"""
        result = self.spotify_skill.play_playlist(playlist_name)
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_pause(self, *args):
        """Handle pausing Spotify"""
        result = self.spotify_skill.pause_playback()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_resume(self, *args):
        """Handle resuming Spotify"""
        result = self.spotify_skill.resume_playback()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_next(self):
        """Handle skipping to next track on Spotify"""
        result = self.spotify_skill.next_track()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_previous(self):
        """Handle going to previous track on Spotify"""
        result = self.spotify_skill.previous_track()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_volume(self, volume_percent):
        """Handle setting Spotify volume"""
        result = self.spotify_skill.set_volume(volume_percent)
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_system_volume(self, action):
        """Handle system volume control"""
        result = self.spotify_skill.control_system_volume(action)
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    def handle_spotify_close(self):
        """Handle closing Spotify"""
        result = self.spotify_skill.close_spotify()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    # --- Reminder handler --- #
    def handle_reminder(self, reminder_text, reminder_time):
        """Handle setting reminders"""
        response = self.time_utility.set_reminder(reminder_text, reminder_time)
        self.speak(response)
        return None
    
    # --- Find my phone handler --- #
    def handle_find_phone(self, *args):
        """Handle finding phone requests"""
        result = self.system_utility.find_my_phone()
        
        if "error" in result:
            self.speak(result["error"])
        else:
            self.speak(result["message"])
        return None
    
    # --- Help and exit handlers --- #
    def show_help(self):
        """Show help information"""
        help_text = f"""{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}
        I can help you with the following:
        • Get the weather (say {Style.BRIGHT}{Fore.RED}'what's the weather'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'weather in [location]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Get weather forecast (say {Style.BRIGHT}{Fore.RED}'forecast'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'forecast for [location]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Get moon phase (say {Style.BRIGHT}{Fore.RED}'what's the moon phase'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'how's the moon tonight'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Get next full moon date (say {Style.BRIGHT}{Fore.RED}'when's the next full moon'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Get internet speed (say {Style.BRIGHT}{Fore.RED}'test my internet speed'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Tell you the time (say {Style.BRIGHT}{Fore.RED}'what time is it'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Tell you the date (say {Style.BRIGHT}{Fore.RED}'what's today's date'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Search the web (say {Style.BRIGHT}{Fore.RED}'search for [query]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Open applications (say {Style.BRIGHT}{Fore.RED}'open [app name]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Open websites (say {Style.BRIGHT}{Fore.RED}'open [website name]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Find your phone (say {Style.BRIGHT}{Fore.RED}'find my phone'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Control Spotify:
        • Play music (say {Style.BRIGHT}{Fore.RED}'play [song name] on Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Pause music (say {Style.BRIGHT}{Fore.RED}'pause Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'stop music'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Resume playback (say {Style.BRIGHT}{Fore.RED}'resume Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'play Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Next track (say {Style.BRIGHT}{Fore.RED}'next song'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'skip song'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Previous track (say {Style.BRIGHT}{Fore.RED}'previous song'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Volume control (say {Style.BRIGHT}{Fore.RED}'volume up'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'volume down'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Close Spotify (say {Style.BRIGHT}{Fore.RED}'close Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'quit Spotify'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Set reminders (say {Style.BRIGHT}{Fore.RED}'remind me to [task] at [time]'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX})
        • Exit (say {Style.BRIGHT}{Fore.RED}'exit'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX} or {Style.BRIGHT}{Fore.RED}'quit'{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}){Style.RESET_ALL}
            """
        
        self.speak("Here are some things I can help you with.", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        print(help_text)
        return None
    
    def exit(self):
        """Exit the assistant"""
        self.speak("Goodbye!", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        self.is_active = False
        return f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Exiting voice assistant.{Style.RESET_ALL}"
    
    def start_voice_mode(self):
        """Start the voice assistant with wake word detection"""
        self.speak("Rub the oil lamp to wake me up.", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
        print(f"{Style.DIM}{Fore.LIGHTGREEN_EX}Voice Assistant is active.{Style.RESET_ALL}")
        print(f"{Style.DIM}{Fore.LIGHTGREEN_EX}Say 'Hey Google', 'Jarvis', or 'Computer' to wake me up.{Style.RESET_ALL}")
        print(f"{Style.DIM}{Fore.LIGHTGREEN_EX}Say 'exit' or 'quit' to end the session.{Style.RESET_ALL}")
        
        # Initialize wake word detector
        wake_detector = WakeWordDetector(
            access_key=self.config["wake_word"]["access_key"],
            wake_words=self.config["wake_word"]["wake_words"],
            sensitivity=self.config["wake_word"]["sensitivity"]
        )
        
        # Start the detector
        if not wake_detector.start():
            self.speak("Failed to start wake word detection.")
            return False
        
        self.is_listening = False
        
        try:
            while self.is_active:
                if not self.is_listening:
                    # Check for wake word using Porcupine
                    detected_word = wake_detector.listen()
                    
                    if detected_word:
                        print(f"{Style.NORMAL}{Fore.LIGHTGREEN_EX}Wake word detected:{Style.RESET_ALL} {Fore.RED}{detected_word}{Style.RESET_ALL}")
                        self.is_listening = True
                        self.speak("State your wish...", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
                        active_until = time.time() + 30  # Active for 30 seconds
                else:
                    # Command listening mode
                    print(f"{Fore.LIGHTRED_EX}Listening for command...{Style.RESET_ALL}")
                    text = self.listen(timeout=3)
                    
                    if text:
                        print(f"{Style.DIM}{Fore.RED}Processing command:{Style.RESET_ALL} {Fore.RED}'{text}'{Style.RESET_ALL}")
                        active_until = time.time() + 30  # Reset active time
                        
                        # Check for exit command
                        if text.strip().lower() in ["exit", "quit", "goodbye", "bye"]:
                            self.speak("Goodbye!")
                            self.is_active = False
                            break
                        
                        # Process the command and get response
                        response = self.process_command(text)
                        
                        # Speak the response if there is one
                        if response:
                            self.speak(response)
                    
                    # Always reset to wake word mode after processing a command or timeout
                    if time.time() > active_until:
                        self.speak("Going back to sleep mode.", f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}")
                        self.is_listening = False
        
        except KeyboardInterrupt:
            print(f"{Style.BRIGHT}{Fore.LIGHTRED_EX}Stopping voice assistant...{Style.RESET_ALL}")
        except Exception as e:
            print(f"Error in voice mode: {e}")
        finally:
            # Clean up resources
            wake_detector.cleanup()
            
        # Clean up resources
        self.engine.stop()
        print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Voice assistant shutdown complete{Style.RESET_ALL}")
        return True
    
    def start_text_mode(self):
        """Start the assistant in text mode"""
        self.speak("Hello. I'm your text assistant. How can I help you today?")
        print("Text Assistant is active. Type your commands and press Enter. Type 'exit' to quit.")
        
        while self.is_active:
            try:
                user_input = input(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}> {Style.RESET_ALL}")
                if user_input.lower() in ["exit", "quit"]:
                    self.exit()
                else:
                    response = self.process_command(user_input.lower())
                    if response:
                        self.speak(response)
            except Exception as e:
                print(f"Error in text mode: {e}")
                
        # Clean up resources
        self.engine.stop()
        return True