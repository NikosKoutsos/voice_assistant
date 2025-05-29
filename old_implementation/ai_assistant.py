import os
import sys
import json
import time
import requests
import webbrowser
import subprocess
import threading
from datetime import datetime,timedelta
import speech_recognition as sr
import pyttsx3
import re
import openai
from difflib import get_close_matches
import pvporcupine
import pyaudio
import struct
import wikipedia
from colorama import init, Fore, Style
import speedtest
# from ctypes import cast, POINTER
# from comtypes import CLSCTX_ALL
# from pycaw import AudioUtilities, IAudioEndpointVolume


class WakeWordDetector:
        
        def __init__(self, access_key, wake_words = None, sensitivity = 0.5):
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
                print(f"Wake word detection has started. Listening for {self.wake_words}")
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
                
class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 200  # Adjust for microphone sensitivity
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Set up API keys
        self.openai_api_key = "sk-proj-YOUR_OPENAI_API_KEY"  # Replace with your OpenAI API key
        self.weather_api_key = "72697e9c2f8b717a7f2633a8189c6861"  # Your weather API key
        
        # Initialize Spotify state
        self.spotify_state = "unknown"
        
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
        
        # Command mapping - maps user phrases to functions
        self.commands = {
            r"weather(?: in| for)? (.+)": self.get_weather,
            r"weather": lambda: self.get_weather("current location"),
            r"forecast(?: in| for)? (.+)": self.get_weather_forecast,
            r"forecast": lambda: self.get_weather_forecast("current location"),
            r"(internet |connection |)(speed test|test speed)":self.run_speedtest,
            r"time": self.get_time,
            r"date|day|today": self.get_date,
            r"find (?:my )?(phone|mobile)": self.find_my_phone,
            r"locate (?:my )?(phone|mobile)": self.find_my_phone,
            r"where(?:'s| is) my (phone|mobile)": self.find_my_phone,
            r"ring (?:my )?(phone|mobile)": self.find_my_phone,
            r"(?:tell me|what is|who is|who was|what are|lookup|search|wikipedia) (?:about |for )?(.*?)(?:\?)?$": self.get_wikipedia_summary,
            r"play (?:the )?(liked songs|discover weekly|release radar|roulette|this is echo tides|this is d|daily mix 1|daily mix 2|daily mix 3|this is evanescence|Final Fantasy VII)(?: on| in)? spotify": self.play_spotify_playlist,
            r"play (.+?)(?: on| in)? spotify": self.play_spotify_song,
            r"(pause|stop) (spotify|music)": self.pause_spotify,
            r"resume (spotify|music)|play spotify|continue music": self.resume_spotify,
            r"next (song|track)|skip (song|track)": lambda *args: self.next_spotify_song("next"),
            r"previous (song|track)|skip (song|track)": lambda *args: self.previous_spotify_song("previous"),
            r"set (?:spotify |music )?volume (?:to )?([\d]+)(?: percent)?": self.set_spotify_volume,        
            r"volume up|increase volume": lambda: self.control_volume("volume_up"),
            r"volume down|decrease volume": lambda: self.control_volume("volume_down"),
            r"close spotify|quit spotify": self.close_spotify,
            r"search for (.+)": self.search_web,
            r"open (?!website|site|page|url)(.+)": self.open_application,
            r"open (website|site|page|url) (.+)": lambda matches: self.open_website(matches.group(2)),
            r"(youtube\.com|youtube|gmail\.com|gmail|google\.com|facebook\.com|twitter\.com|reddit\.com|netflix\.com|google\.com|claude\.ai)": self.open_website,
            r"remind me to (.+) at (.+)": self.set_reminder,
            r"help|what can you do": self.show_help,
            r"exit|quit|stop|goodbye": self.exit
        }

    def speak(self, text):
        """Convert text to speech"""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, timeout=None):
        """Listen for user speech and convert to text"""
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {Fore.YELLOW}{text}{Style.RESET_ALL}")
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

    # def get_ai_response(self, query):
    #     """Get response from OpenAI API"""
    #     try:
    #         openai.api_key = self.openai_api_key
    #         response = openai.ChatCompletion.create(
    #             model="gpt-3.5-turbo",
    #             messages=[
    #                 {"role": "system", "content": "You are a helpful assistant integrated into a Windows application."},
    #                 {"role": "user", "content": query}
    #             ],
    #             max_tokens=150
    #         )
    #         return response.choices[0].message.content.strip()
    #     except Exception as e:
    #         return f"Sorry, I couldn't get a response from the AI service. Error: {e}"

    def run_speedtest(self, *args):
            """Perform a speed test"""
            
            self.speak("Starting the speed test, hold fast bitch")
            
            try:
                st = speedtest.Speedtest()
                self.speak("Finding the best server...")
                st.get_best_server()
                
                self.speak("Testing download speed...")
                download_speed = st.download() / 1_000_000  # Convert to Mbps
                
                self.speak("Testing upload speed...")
                upload_speed = st.upload() / 1_000_000  # Convert to Mbps
                
                ping = st.results.ping
                
                result = f"Speed test results: Download speed: {download_speed:.2f} Mbps, Upload speed: {upload_speed:.2f} Mbps, Ping: {ping} ms"
                
                self.speak(f"Your download speed is {download_speed:.1f} megabits per second, upload speed is {upload_speed:.1f} megabits per second, and ping is {ping} milliseconds.")
                
                print(result)
                return None
            except Exception as e:
                print(f"Error running speed test: {e}")
                self.speak("Sorry, I couldn't perform the speed test.")
                return None

    def find_my_phone(self, *args):
        """Open Google's Find My Device service to help locate an Android phone
        
        Returns:
            str: Status message about the phone locating attempt
        """
        self.speak("Opening Google Find My Device to locate your phone")
        
        try:
            # Open Google's Find My Device service
            webbrowser.open("https://android.com/find")
            
            # Provide clear instructions
            self.speak("Once the page loads, click on your device and select Play Sound to make it ring at full volume")
            
            # Return None so we don't repeat the instructions
            return None
                
        except Exception as e:
            print(f"Error opening Find My Device: {e}")
            return f"I encountered an error while trying to open Find My Device: {e}"
    
    def match_location(self, spoken_location):
        """Match spoken location to a list of known locations using fuzzy matching"""
        known_locations = ["Lamia", "Athens", "Thessaloniki", "Patras", "Heraklion"]
        
        # Try exact match first (case insensitive)
        for loc in known_locations:
            if spoken_location.lower() == loc.lower():
                return loc
        
        # Try fuzzy matching
        matches = get_close_matches(spoken_location, known_locations, n=1, cutoff=0.6)
        
        if matches:
            print(f"Matched '{spoken_location}' to '{matches[0]}'")
            return matches[0]
        
        return spoken_location
    
    def get_weather(self, location):
        """Get current weather for a location"""
        self.speak(f"Getting weather information for {location}")
        
        location = self.match_location(location)  # Match location to known locations
        
        try:
            # Handle current location detection
            if location.lower() in ["current location", "here", "my location"]:
                try:
                    ip_info = requests.get("https://ipinfo.io/json").json()
                    if "city" in ip_info and "country" in ip_info:
                        location = f"{ip_info['city']}, {ip_info['country']}"
                        print(f"Detected location: {location}")
                except:
                    print("Could not detect location. Using default.")
            
            # Encode the location for the URL
            encoded_location = requests.utils.quote(location)
            
            # Get weather data
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_location}&appid={self.weather_api_key}&units=metric"
            response = requests.get(weather_url)
            
            if response.status_code == 200:
                weather_data = response.json()
                
                # Format the weather data
                city_name = weather_data['name']
                country = weather_data['sys']['country']
                temp = round(weather_data['main']['temp'])
                temp_f = round((temp * 9/5) + 32)  # Convert to F for reference
                condition = weather_data['weather'][0]['main']
                description = weather_data['weather'][0]['description']
                humidity = weather_data['main']['humidity']
                wind_speed = round(weather_data['wind']['speed'])
                wind_dir = self.get_wind_direction(weather_data['wind']['deg'])
                
                # Format complete response
                weather_info = f"Current weather in {city_name}, {country}: "
                weather_info += f"Temperature: {temp}°C ({temp_f}°F), "
                weather_info += f"Conditions: {description}, "
                weather_info += f"Humidity: {humidity}%, "
                weather_info += f"Wind: {wind_speed} km/h from the {wind_dir}"
                
                # Only speak a summary, not the full details
                self.speak(f"It's currently {temp}°C with {description} in {city_name}")
                
                # Just return the detailed info but don't speak it again
                print(weather_info)
                return None  # Return None so process_command won't speak the response again
            else:
                error_info = f"Couldn't get weather: {response.status_code} - {response.reason}"
                self.speak(f"Sorry, I couldn't find weather information for {location}")
                return None  # Don't duplicate error message
                    
        except Exception as e:
            error_info = f"Error getting weather: {e}"
            self.speak("Sorry, there was an error getting the weather information")
            return None  # Don't duplicate error message

    def get_weather_forecast(self, location):
        """Get weather forecast for a location"""
        self.speak(f"Getting weather forecast for {location}")
        
        location = self.match_location(location)  # Match location to known locations
        
        try:
            # Handle current location detection
            if location.lower() in ["current location", "here", "my location"]:
                try:
                    ip_info = requests.get("https://ipinfo.io/json").json()
                    if "city" in ip_info and "country" in ip_info:
                        location = f"{ip_info['city']}, {ip_info['country']}"
                        print(f"Detected location: {location}")
                except:
                    print("Could not detect location. Using default.")
            
            # Encode the location for the URL
            encoded_location = requests.utils.quote(location)
            
            # Get forecast data - use metric units for Celsius
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={encoded_location}&appid={self.weather_api_key}&units=metric"
            response = requests.get(forecast_url)
            
            if response.status_code == 200:
                forecast_data = response.json()
                
                # Format the forecast
                city_name = forecast_data['city']['name']
                forecast_text = f"Weather forecast for {city_name}:\n"
                
                # Track unique days and their forecast info
                processed_days = {}
                day_forecasts = {}
                today = datetime.now().strftime("%Y-%m-%d")
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                for forecast in forecast_data['list']:
                    # Parse the date
                    forecast_date = datetime.fromtimestamp(forecast['dt'])
                    forecast_day = forecast_date.strftime("%Y-%m-%d")
                    
                    # Only process each day once and limit to 3 days
                    if forecast_day not in processed_days and len(processed_days) < 3:
                        processed_days[forecast_day] = True
                        
                        # Get weather info
                        description = forecast['weather'][0]['description']
                        temp_min = round(forecast['main']['temp_min'])
                        temp_max = round(forecast['main']['temp_max'])
                        
                        # Set the day name
                        if forecast_day == today:
                            day_name = "Today"
                        elif forecast_day == tomorrow:
                            day_name = "Tomorrow"
                        else:
                            day_name = forecast_date.strftime("%A")
                        
                        # Store the forecast info
                        day_forecasts[day_name] = {
                            'description': description,
                            'high': temp_max,
                            'low': temp_min
                        }
                        
                        # Add to the text output
                        forecast_text += f"{day_name}: {description} with a high of {temp_max}°C and a low of {temp_min}°C\n"
                
                # Speak the forecast
                self.speak(f"Here's the forecast for {city_name}")
                for day_name, forecast_info in day_forecasts.items():
                    self.speak(f"{day_name}: {forecast_info['description']} with a high of {forecast_info['high']}°C and a low of {forecast_info['low']}°C")
                
                print(forecast_text)
                return None
            else:
                error_info = f"Couldn't get forecast: {response.status_code} - {response.reason}"
                self.speak(f"Sorry, I couldn't find forecast information for {location}")
                return None
                    
        except Exception as e:
            error_info = f"Error getting forecast: {e}"
            self.speak("Sorry, there was an error getting the forecast information")
            print(f"Forecast error details: {e}")
            return None

    def get_wind_direction(self, degrees):
        """Convert wind degrees to cardinal direction"""
        directions = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest", "north"]
        index = round(degrees / 45)
        return directions[index]

    def get_time(self):
        """Get current time"""
        current_time = datetime.now().strftime("%I:%M %p")
        response = f"The current time is {current_time}."
        self.speak(response)
        return None

    def get_date(self):
        """Get current date"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        response = f"Today is {current_date}."
        self.speak(response)
        return None
    
    def get_wikipedia_summary(self, query):
        """ Get A summary from wikipedia """
        self.speak(f"Bitch let me find out about {query}")
        
        try:
            summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
            
            summary = summary.replace("( listen)", "").replace(" ", " ")
            
            self.speak(f"According to Wikipedia:{summary[:300]}...")
            print(f"Wikipedia summer for {query}:\n{summary}")
            return None
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[5]
            options_text = ", ".join(options)
            self.speak(f"There are multiple results for {query}. Options include: {options_text}")
            return None
        except wikipedia.exceptions.PageError:
            return f"Sorry, I couldn't find any Wikipedia Information about {query}"
        except Exception as e:
            print(f"Error getting Wikipedia summary:{e}")
            return f"Sorry, I had trouble accessing Wikipedia {e}"
        
        
    def play_spotify_song(self, song_name):
        """Play a song on Spotify using Spotipy with device handling"""
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        self.speak(f"Searching for {song_name} on Spotify")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            #   Initialize Spotipy client with OAuth
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state"
            ))
            
            #check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            # Search for the track
            results = sp.search(q=song_name, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_uri = track['uri']
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                
                # Play the track on the active device
                if device_id:
                    sp.start_playback(device_id=device_id, uris=[track_uri])
                else:
                    sp.start_playback(uris=[track_uri])  # Try without specifying device
                
                return f"Playing {track_name} by {artist_name} on Spotify."
            else:
                return f"Sorry, I couldn't find {song_name} on Spotify."
                
        except Exception as e:
            print(f"Error playing Spotify track: {e}")
            
            # If we get a 404 with NO_ACTIVE_DEVICE, give more helpful instructions
            if "NO_ACTIVE_DEVICE" in str(e):
                return "I found the song but Spotify isn't running on any device. Please open Spotify and try again."
            
            return f"Sorry, I had trouble controlling Spotify: {e}"
    
    def play_spotify_playlist(self, playlist_name):
        """Play a playlist on Spotify with reliable matching"""
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Debug info
        print(f"Recognized playlist request: '{playlist_name}'")
        
        # Clean the input
        playlist_name_lower = playlist_name.lower().strip()
        
        try:
            # Authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private"
            ))
            
            # Check for devices
            devices = sp.devices()
            if not devices['devices']:
                self.speak("No Spotify devices found. Opening Spotify.")
                try:
                    subprocess.Popen("start spotify:", shell=True)
                    time.sleep(5)
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually."
            
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            # Known playlists with name variations
            known_playlists = {
                "spotify:playlist:37i9dQZF1DZ06evO2hpj2Q": ["echo tides", "this is echo tides"],
                "spotify:playlist:37i9dQZF1DZ06evO2IQ4xi": ["this is d", "this is d"],
                "spotify:playlist:37i9dQZF1DZ06evO3aj2q4": ["this is evanescense", "this is evanescence"],
                "spotify:playlist:37i9dQZEVXcJZyENOWUFo7": ["discover weekly"],
                "spotify:playlist:37i9dQZEVXbmQmFX5U86jr": ["release radar"],
                "spotify:playlist:37i9dQZF1FbCK3af0rHqCR": ["roulette"],
                "spotify:collection:tracks": ["liked songs", "my liked songs", "saved songs", "favorites"],
                "spotify:playlist:37i9dQZF1E35xxvOcsuPqR": ["daily mix 1"],
                "spotify:playlist:37i9dQZF1E3507niki8GrC": ["daily mix 2"],
                "spotify:playlist:37i9dQZF1E3ai3nFsonfrE": ["daily mix 3"],
                "spotify:playlist:4zv8L6EVSRuUDQ3JTrbbhn": ["Final Fantasy VII"],     
            }
            
            # Variable to track if playback started successfully
            playback_started = False
            playlist_name_display = playlist_name  # Default display name
            
            # Try to match with known playlists
            for uri, variations in known_playlists.items():
                # Check for exact matches first
                if playlist_name_lower in variations:
                    print(f"Found exact match: {playlist_name_lower}")
                    playlist_name_display = variations[0]
                    self.speak(f"Playing {playlist_name_display}")
                    sp.start_playback(device_id=device_id, context_uri=uri)
                    playback_started = True
                    break
            
            # If not found in exact matches, try partial matches
            if not playback_started:
                for uri, variations in known_playlists.items():
                    for variation in variations:
                        if variation in playlist_name_lower:
                            print(f"Found partial match: {variation} in {playlist_name_lower}")
                            playlist_name_display = variations[0]
                            self.speak(f"Playing {playlist_name_display}")
                            sp.start_playback(device_id=device_id, context_uri=uri)
                            playback_started = True
                            break
                    if playback_started:
                        break
            
            # If still not found, search user's playlists
            if not playback_started:
                self.speak(f"Searching for {playlist_name}")
                
                # First try user's own playlists
                playlists = []
                results = sp.current_user_playlists(limit=50)
                playlists.extend(results['items'])
                
                for playlist in playlists:
                    if playlist_name_lower in playlist['name'].lower():
                        playlist_name_display = playlist['name']
                        self.speak(f"Playing your playlist {playlist_name_display}")
                        sp.start_playback(device_id=device_id, context_uri=playlist['uri'])
                        playback_started = True
                        break
            
            # Last resort: search Spotify
            if not playback_started:
                results = sp.search(q=playlist_name, type='playlist', limit=1)
                if results['playlists']['items']:
                    found = results['playlists']['items'][0]
                    playlist_name_display = found['name']
                    self.speak(f"Playing {playlist_name_display} by {found['owner']['display_name']}")
                    sp.start_playback(device_id=device_id, context_uri=found['uri'])
                    playback_started = True
            
            # If playback started successfully, check what's playing
            if playback_started:
                # Use the helper method to display the currently playing track
                self.get_currently_playing(sp)
            
            # Return appropriate message (but don't speak it again)
            if playback_started:
                return None  # Return None to prevent double-speaking
            else:
                return f"Sorry, I couldn't find a playlist called {playlist_name}"
                
        except Exception as e:
            print(f"Error playing playlist: {e}")
            return f"Sorry, I encountered an error: {e}"
        
    def get_currently_playing(self, sp):
        """Helper method to display currently playing track
        
        Args:
            sp: An authenticated Spotipy client with appropriate scopes
            
        Returns:
            None
        """
        try:
            time.sleep(4)  # Wait for Spotify to update
            
            current = sp.current_playback()
            if current and 'item' in current and current['item']:
                track = current['item']
                artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                track_name = track['name']
                
                # Add album info if available
                album_name = track['album']['name'] if 'album' in track and 'name' in track['album'] else None

                
                if album_name:
                    print(f"{Fore.YELLOW}▶️ {Fore.GREEN}Now playing: {Style.RESET_ALL}{track_name} {Fore.CYAN}by {artist_name} - Album: {album_name}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}▶️ {Fore.GREEN}Now playing: {Style.RESET_ALL}{track_name} {Fore.CYAN}by {artist_name}{Style.RESET_ALL}")
                
                return {
                    "track": track_name,
                    "artist": artist_name,
                    "album": album_name
                }
            return None
        except Exception as e:
            print(f"Error getting current track: {e}")
            return None

    def pause_spotify(self, *args):
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        self.speak(f"Pausing Spotify")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            #   Initialize Spotipy client with OAuth
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state"
            ))
            
            #check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            #pause playback
            sp.pause_playback(device_id=device_id)
            
            return "Paused playback on Spotify."
        except Exception as e:
            print(f"Error pausing Spotify: {e}")
            return f"Sorry, I had trouble pausing Spotify: {e}"
            

    def resume_spotify(self, *args):
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        self.speak(f"Resuming Spotify")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            #   Initialize Spotipy client with OAuth
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state"
            ))
            
            #check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            #resume playback
            sp.start_playback(device_id=device_id)
            
            return "Resumed playback on Spotify."
        except Exception as e:
            print(f"Error resuming Spotify: {e}")
            return f"Sorry, I had trouble resuming Spotify: {e}"
    
    def next_spotify_song(self, action = None):
        """Skip to the next song on Spotify"""
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        self.speak(f"Skipping to the next song on Spotify")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            # Initialize Spotipy client with OAuth - note the addition of user-read-currently-playing
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
            ))
            
            # Check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            # Skip to the next track
            sp.next_track(device_id=device_id)
            
            # Use the helper method to display the currently playing track
            self.get_currently_playing(sp)
            
            return None  # Return None to prevent double-speaking
        except Exception as e:
            print(f"Error skipping track on Spotify: {e}")
            return f"Sorry, I had trouble skipping the track on Spotify: {e}"
        

    def previous_spotify_song(self, action = None):
        """Skip to the previous song on Spotify"""
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        self.speak(f"Skipping to the previous song on Spotify")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            # Initialize Spotipy client with OAuth - note the addition of user-read-currently-playing
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing"
            ))
            
            # Check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            # Skip to the previous track
            sp.previous_track(device_id=device_id)
            
            # Use the helper method to display the currently playing track
            self.get_currently_playing(sp)
            
            return None  # Return None to prevent double-speaking
        except Exception as e:
            print(f"Error going to previous track on Spotify: {e}")
            return f"Sorry, I had trouble going to the previous track on Spotify: {e}"

    def set_spotify_volume(self, volume_percent):
        """Set Spotify volume to a specific percentage"""
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Convert string percentage to integer if needed
        try:
            volume_level = int(volume_percent)
            # Ensure volume is within valid range (0-100)
            volume_level = max(0, min(100, volume_level))
        except ValueError:
            return f"Sorry, I couldn't understand that volume level. Please specify a number between 0 and 100."
        
        self.speak(f"Setting Spotify volume to {volume_level} percent")
        
        try:
            # authentication
            client_id = '90e41118f3574a15affe5b56609c75c1'
            client_secret = '2a7b8b8d8cea418b84356b9201472ce8'
            redirect_uri = 'http://localhost:8888/callback'
            
            # Initialize Spotipy client with OAuth
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="user-read-playback-state,user-modify-playback-state"
            ))
            
            # Check for available devices
            devices = sp.devices()
            
            # If no active devices, try to launch Spotify
            if not devices['devices']:
                self.speak("No active Spotify devices found. Let me try to open Spotify for you.")
                try:
                    # Launch Spotify app
                    subprocess.Popen("start spotify:", shell=True)
                    # Wait for Spotify to open
                    time.sleep(5)
                    
                    # Check for devices again
                    devices = sp.devices()
                    if not devices['devices']:
                        return "Please open Spotify manually and try again. Spotify needs to be running to control it."
                except Exception as e:
                    print(f"Error launching Spotify: {e}")
                    return "Please open Spotify manually and try again."
            
            # Get the first available device
            device_id = devices['devices'][0]['id'] if devices['devices'] else None
            
            # Set volume
            sp.volume(volume_level, device_id=device_id)
            
            return f"Set Spotify volume to {volume_level} percent."
        except Exception as e:
            print(f"Error setting Spotify volume: {e}")
            return f"Sorry, I had trouble setting the volume: {e}"
            
    
    def control_volume(self, action):
        """Control Spotify playback with improved volume controls"""
        self.speak(f"Controlling System volume: {action}")
        
        try:               
            if action == "volume_up":
                # Increase system volume by approximately 20%
                # Each press is roughly 2%, so 10 presses ≈ 20%
                try:
                    for _ in range(10):
                        # Send VK_VOLUME_UP (0xAF)
                        from ctypes import windll
                        windll.user32.keybd_event(0xAF, 0, 0, 0)  # key down
                        windll.user32.keybd_event(0xAF, 0, 2, 0)  # key up
                        time.sleep(0.05)  # Small delay between presses
                    return "Increased volume by about 20 percent."
                except Exception as e:
                    print(f"Error using direct volume controls: {e}")
                    # Fallback to PowerShell for volume up
                    for _ in range(10):
                        subprocess.run('powershell -Command "(New-Object -com wscript.shell).SendKeys([char]175)"', shell=True)
                        time.sleep(0.05)
                    return "Increased volume by about 20 percent."
                
            elif action == "volume_down":
                # Decrease system volume by approximately 20%
                try:
                    for _ in range(10):
                        # Send VK_VOLUME_DOWN (0xAE)
                        from ctypes import windll
                        windll.user32.keybd_event(0xAE, 0, 0, 0)  # key down
                        windll.user32.keybd_event(0xAE, 0, 2, 0)  # key up
                        time.sleep(0.05)  # Small delay between presses
                    return "Decreased volume by about 20 percent."
                except Exception as e:
                    print(f"Error using direct volume controls: {e}")
                    # Fallback to PowerShell for volume down
                    for _ in range(10):
                        subprocess.run('powershell -Command "(New-Object -com wscript.shell).SendKeys([char]174)"', shell=True)
                        time.sleep(0.05)
                    return "Decreased volume by about 20 percent."
                
            else:
                return f"Unknown Spotify control action: {action}"
                
        except Exception as e:
            print(f"Error controlling playback: {e}")
            return f"I had trouble controlling the playback: {e}"

    def close_spotify(self):
        """Close Spotify"""
        self.speak("Closing Spotify")
        
        try:
            platform = sys.platform
            
            if platform == "win32":
                subprocess.call("taskkill /F /IM spotify.exe", shell=True)
            elif platform == "darwin":  # macOS
                subprocess.call(["killall", "Spotify"])
            elif platform.startswith("linux"):
                subprocess.call(["killall", "spotify"])
            else:
                return "Sorry, Spotify control is not supported on this platform."
                
            return "Closed Spotify."
            
        except Exception as e:
            return f"Sorry, I had trouble closing Spotify: {e}"

    def search_web(self, query):
        """Search the web for a query"""
        self.speak(f"Searching the web for {query}")
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.quote(query)}")
        return f"I've opened a web search for '{query}'."

    def open_application(self, app_name):
        """Open an application"""
        self.speak(f"Opening {app_name}")
        
        # Common apps mapping
        common_apps = {
            "steam": "steam://open/main",
            "epic games": "com.epicgames.launcher://apps",
            "epic": "com.epicgames.launcher://apps",
            "discord": "discord://",
            "slack": "slack://",
            "xbox": "xbox://",
            "outlook": "outlook:",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "teams": "msteams:",
            "vs code": "code",
            "visual studio code": "code",
            "visual studio": "devenv",
            "stremio": "stremio://"
        }
        
        try:
            app_name = app_name.strip().lower()
            platform = sys.platform
            
            # Check for common apps first
            if app_name in common_apps:
                if platform == "win32":
                    subprocess.Popen(f"start {common_apps[app_name]}", shell=True)
                elif platform == "darwin":  # macOS
                    subprocess.Popen(["open", common_apps[app_name]])
                elif platform.startswith("linux"):
                    subprocess.Popen(["xdg-open", common_apps[app_name]])
                return f"Opening {app_name} now."
            
            # Try a direct approach
            if platform == "win32":
                subprocess.Popen(f"start {app_name}", shell=True)
            elif platform == "darwin":  # macOS
                subprocess.Popen(["open", "-a", app_name])
            elif platform.startswith("linux"):
                subprocess.Popen([app_name])
            
            return f"Opening {app_name} now."
            
        except Exception as e:
            return f"Sorry, I couldn't open {app_name}: {e}"

    def open_website(self, website_name):
        """Open a website"""
        self.speak(f"Opening {website_name}")
        
        # Common website mappings
        websites = {
            "youtube": "https://www.youtube.com",
            "youtube.com": "https://www.youtube.com",
            "gmail": "https://mail.google.com",
            "gmail.com": "https://mail.google.com",
            "google": "https://www.google.com",
            "google.com": "https://www.google.com",
            "facebook": "https://www.facebook.com",
            "facebook.com": "https://www.facebook.com",
            "twitter": "https://twitter.com",
            "twitter.com": "https://twitter.com",
            "instagram": "https://www.instagram.com",
            "instagram.com": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "linkedin.com": "https://www.linkedin.com",
            "reddit": "https://www.reddit.com",
            "reddit.com": "https://www.reddit.com",
            "netflix": "https://www.netflix.com",
            "netflix.com": "https://www.netflix.com",
            "amazon": "https://www.amazon.com",
            "amazon.com": "https://www.amazon.com",
            "twitch": "https://www.twitch.tv",
            "twitch.tv": "https://www.twitch.tv",
            "github": "https://github.com",
            "github.com": "https://github.com",
            "netflix.com": "https://www.netflix.com/browse",
            "claude.ai": "https://claude.ai"
        }
        
        website_name = website_name.lower()
        
        # Check if it's a known website
        if website_name in websites:
            webbrowser.open(websites[website_name])
            return f"Opening {website_name} now."
        
        # Check if it's a URL with http/https
        if website_name.startswith(("http://", "https://")):
            webbrowser.open(website_name)
            return f"Opening {website_name} now."
        
        # Check if it ends with a common TLD
        if re.search(r"\.(com|org|net|edu|gov|io|tv)$", website_name):
            webbrowser.open(f"https://{website_name}")
            return f"Opening {website_name} now."
        
        # Default - Try adding www. and .com
        try:
            webbrowser.open(f"https://www.{website_name}.com")
            return f"Opening {website_name} now."
        except:
            return f"Sorry, I couldn't open the website {website_name}."

    def set_reminder(self, reminder_text, reminder_time):
        """Set a reminder"""
        self.speak(f"Setting a reminder for {reminder_text} at {reminder_time}")
        
        # This would typically integrate with a scheduling system
        # For demonstration, we'll just log it
        print(f"REMINDER SET: {reminder_text} at {reminder_time}")
        
        return f"I've set a reminder for '{reminder_text}' at {reminder_time}."

    def show_help(self):
        """Show help information"""
        help_text = """
I can help you with the following:
- Get the weather (say 'what's the weather' or 'weather in [location]')
- Get weather forecast (say 'forecast' or 'forecast for [location]')
- Tell you the time (say 'what time is it')
- Tell you the date (say 'what's today's date')
- Search the web (say 'search for [query]')
- Open applications (say 'open [app name]')
- Open websites (say 'open [website name]')
- Find your phone (say 'find my phone')
- Control Spotify:
  • Play music (say 'play [song name] on Spotify')
  • Pause music (say 'pause Spotify' or 'stop music')
  • Resume playback (say 'resume Spotify' or 'play Spotify')
  • Next track (say 'next song' or 'skip song')
  • Previous track (say 'previous song')
  • Volume control (say 'volume up' or 'volume down')
  • Close Spotify (say 'close Spotify' or 'quit Spotify')
- Set reminders (say 'remind me to [task] at [time]')
- Exit (say 'exit' or 'quit')
        """
        
        self.speak("Here are some things I can help you with.")
        print(help_text)
        return help_text

    def exit(self):
        """Exit the assistant"""
        self.speak("Goodbye!")
        self.is_active = False
        return "Exiting voice assistant."

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
        
        # If no command matched, use AI response
        # return self.get_ai_response(text)                

    def start_voice_mode(self):
        """Start the voice assistant with wake word detection"""
        self.speak("Bitch you better not wake me up")
        print("Voice Assistant is active.")
        print("Say 'Hey Google', 'Jarvis', or 'Computer' to wake me up.")
        print("Say 'exit' or 'quit' to end the session.")
        
        # Initialize wake word detector
        wake_detector = WakeWordDetector(
            access_key="2hs/UmBDGlm0oCWqGVFzavxI6Manb3VZtiWoJ/0J1U/qargkzDHs6A==",
            wake_words=["jarvis", "computer", "hey google"],
            sensitivity=0.7
        )
        
        # Start the detector
        if not wake_detector.start():
            self.speak("Failed to start wake word detection.")
            return self.start_voice_mode()
        
        self.is_listening = False
        
        try:
            while self.is_active:
                if not self.is_listening:
                    # Check for wake word using Porcupine
                    detected_word = wake_detector.listen()
                    
                    if detected_word:
                        print(f"Wake word detected: {detected_word}")
                        self.is_listening = True
                        self.speak("I'm awake..")
                        active_until = time.time() + 30  # Active for 30 seconds
                else:
                    # Command listening mode
                    print("Listening for command...")
                    text = self.listen(timeout=7)
                    
                    if text:
                        print(f"Processing command: '{text}'")
                        active_until = time.time() + 30 # Reset active time
                        
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
                    
                    # Always reset to wake word mode after processing a command
                    if time.time() > active_until:
                        self.speak("Going back to bed.")
                        self.is_listening = False
        
        except KeyboardInterrupt:
            print("Stopping voice assistant...")
        except Exception as e:
            print(f"Error in voice mode: {e}")
        finally:
            # Clean up resources
            wake_detector.cleanup()
            
        # Clean up resources
        print("Shutting down voice assistant...")
        self.engine.stop()
        print("Voice assistant shutdown complete")

    def start_text_mode(self):
        """Start the assistant in text mode"""
        self.speak("Hello Bitch. What do you need?")
        print("Text Assistant is active. Type your commands and press Enter. Type 'exit' to quit.")
        
        while self.is_active:
            try:
                user_input = input("> ")
                if user_input.lower() in ["exit", "quit"]:
                    self.exit()
                else:
                    self.process_command(user_input.lower())
            except Exception as e:
                print(f"Error in text mode: {e}")
                
        # Clean up resources
        self.engine.stop()

def main():
    """Main function to start the assistant"""
    assistant = VoiceAssistant()
    
    print("Which assistant would you like to start?")
    print("1. Voice Assistant")
    print("2. Text Assistant")
    
    choice = input("Enter 1 or 2: ")
    
    if choice == "1":
        assistant.start_voice_mode()
    else:
        assistant.start_text_mode()

if __name__ == "__main__":
    main()