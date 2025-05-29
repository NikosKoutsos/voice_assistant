import time
import os
import subprocess
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from colorama import Fore, Style
from dotenv import load_dotenv

class SpotifySkill:
    
    load_dotenv()  # Load environment variables from .env file
    
    def __init__(self, client_id, client_secret, redirect_uri):
        """Initialize the Spotify skill with authentication details"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,playlist-read-private"
    
    def _get_spotify_client(self):
        """Get an authenticated Spotify client"""
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        ))
    
    def _ensure_active_device(self, sp=None, prefer_computer=True):
        """Ensure there's an active Spotify device, opening Spotify if needed"""
        if sp is None:
            sp = self._get_spotify_client()
            
        devices = sp.devices()
        
        if not devices['devices']:
            print("No active Spotify devices found. Opening Spotify.")
            try:
                subprocess.Popen("start spotify:", shell=True)
                time.sleep(5)  # Give Spotify time to start
                devices = sp.devices()
                if not devices['devices']:
                    return None, "Please open Spotify manually and try again."
            except Exception as e:
                print(f"Error launching Spotify: {e}")
                return None, "Please open Spotify manually and try again."
        
        if prefer_computer and devices['devices']:
            computer_devices = [d for d in devices['devices']
                               if 'smartphone' not in d['type'].lower()
                               and 'mobile' not in d['type'].lower()
                               and 'phone' not in d['type'].lower()]
            if computer_devices:
                print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Selected computer device:{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{computer_devices[0]['name']}{Style.RESET_ALL}")
                return computer_devices[0]['id'], None
        
        device_id = devices['devices'][0]['id'] if devices['devices'] else None
        if devices['devices']:
            print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Selected device:{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{devices['devices'][0]['name']}{Style.RESET_ALL}")
        
        return device_id, None
    
    def play_song(self, song_name):
        """Play a song on Spotify"""
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            # Search for the track
            results = sp.search(q=song_name, type='track', limit=5)
            
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
                
                # Get info about what's now playing
                current_track_info = self.get_currently_playing(sp)
                
                return {
                    "success": True,
                    "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Playing{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{track_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}by{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{artist_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}on Spotify.{Style.RESET_ALL}",
                    "current_track": current_track_info
                }
            else:
                return {
                    "success": False, 
                    "error": f"Sorry, I couldn't find {song_name} on Spotify."
                }
                
        except Exception as e:
            print(f"Error playing Spotify track: {e}")
            
            # If we get a 404 with NO_ACTIVE_DEVICE, give more helpful instructions
            if "NO_ACTIVE_DEVICE" in str(e):
                return {
                    "success": False,
                    "error": "I found the song but Spotify isn't running on any device. Please open Spotify and try again."
                }
            
            return {
                "success": False,
                "error": f"Sorry, I had trouble controlling Spotify: {e}"
            }
    
    def play_playlist(self, playlist_name):
        """Play a playlist on Spotify with reliable matching"""
        
        echo_tides = os.getenv("echo_tides")
        this_is_doechii = os.getenv("this_is_doechii")
        this_is_evanescense = os.getenv("this_is_evanescense")
        discover_weekly = os.getenv("discover_weekly")
        release_radar = os.getenv("release_radar")
        daylist_roulette = os.getenv("daylist_roulette")
        favorite_songs = os.getenv("favorite_songs")
        daily_mix_1 = os.getenv("daily_mix_1")
        daily_mix_2 = os.getenv("daily_mix_2")
        daily_mix_3 = os.getenv("daily_mix_3")
        final_fantasy_vii = os.getenv("final_fantasy_vii")
        this_is_my_chemical_romance = os.getenv("this_is_my_chemical_romance")
        this_is_agnes_obel = os.getenv("this_is_agnes_obel")

        # Debug info
        print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Recognized playlist request:{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}'{playlist_name}'{Style.RESET_ALL}")
        
        # Clean the input
        playlist_name_lower = playlist_name.lower().strip()
        
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            # Known playlists with name variations
            known_playlists = {
                echo_tides: ["echo tides", "this is echo tides"],
                this_is_doechii: ["this is d", "this is d"],
                this_is_evanescense: ["this is evanescense", "this is evanescence"],
                discover_weekly: ["discover weekly"],
                release_radar: ["release radar"],
                daylist_roulette: ["roulette"],
                favorite_songs: ["liked songs", "my liked songs", "saved songs", "favorites"],
                daily_mix_1: ["daily mix 1"],
                daily_mix_2: ["daily mix 2"],
                daily_mix_3: ["daily mix 3"],
                final_fantasy_vii: ["Final Fantasy VII"],
                this_is_my_chemical_romance: ["this is My Chemical Romance", "my chemical romance"],
                this_is_agnes_obel: ["this is agnes obel"]
            }
            
            # Variable to track if playback started successfully
            playback_started = False
            playlist_name_display = playlist_name  # Default display name
            
            # Try to match with known playlists
            for uri, variations in known_playlists.items():
                # Check for exact matches first
                if playlist_name_lower in variations:
                    print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Found exact match:{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{playlist_name_lower}{Style.RESET_ALL}")
                    playlist_name_display = variations[0]
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
                            sp.start_playback(device_id=device_id, context_uri=uri)
                            playback_started = True
                            break
                    if playback_started:
                        break
            
            # If still not found, search user's playlists
            if not playback_started:
                # First try user's own playlists
                playlists = []
                results = sp.current_user_playlists(limit=50)
                playlists.extend(results['items'])
                
                for playlist in playlists:
                    if playlist_name_lower in playlist['name'].lower():
                        playlist_name_display = playlist['name']
                        sp.start_playback(device_id=device_id, context_uri=playlist['uri'])
                        playback_started = True
                        break
            
            # Last resort: search Spotify
            if not playback_started:
                results = sp.search(q=playlist_name, type='playlist', limit=5)
                if results['playlists']['items']:
                    found = results['playlists']['items'][0]
                    playlist_name_display = found['name']
                    owner_name = found['owner']['display_name']
                    sp.start_playback(device_id=device_id, context_uri=found['uri'])
                    playback_started = True
            
            # If playback started successfully, check what's playing
            if playback_started:
                # Get the currently playing track
                current_track_info = self.get_currently_playing(sp)
                
                return {
                    "success": True,
                    "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Playing{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{playlist_name_display}{Style.RESET_ALL}",
                    "current_track": current_track_info
                }
            else:
                return {
                    "success": False,
                    "error": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Sorry, I couldn't find a playlist called{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}{playlist_name}{Style.RESET_ALL}"
                }
                
        except Exception as e:
            print(f"Error playing playlist: {e}")
            return {
                "success": False,
                "error": f"Sorry, I encountered an error: {e}"
            }
    
    def get_currently_playing(self, sp=None):
        """Get information about the currently playing track"""
        if sp is None:
            sp = self._get_spotify_client()
            
        try:
            time.sleep(2)  # Wait for Spotify to update
            
            current = sp.current_playback()
            if current and 'item' in current and current['item']:
                track = current['item']
                artist_name = track['artists'][0]['name'] if track['artists'] else 'Unknown Artist'
                track_name = track['name']
                
                # Add album info if available
                album_name = track['album']['name'] if 'album' in track and 'name' in track['album'] else None

                # Print colorful output
                if album_name:
                    print(f"▶️ {Style.BRIGHT}{Fore.LIGHTGREEN_EX}Now playing:{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{track_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}by {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{artist_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTGREEN_EX}- Album:{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{album_name}{Style.RESET_ALL}{Style.RESET_ALL}")
                else:
                    print(f"▶️ {Style.BRIGHT}{Fore.LIGHTGREEN_EX}Now playing:{Style.RESET_ALL}{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{track_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.CYAN}by {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{artist_name}{Style.RESET_ALL}")
                
                return {
                    "track": track_name,
                    "artist": artist_name,
                    "album": album_name
                }
            return None
        except Exception as e:
            print(f"Error getting current track: {e}")
            return None
    
    def pause_playback(self):
        """Pause Spotify playback"""
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            sp.pause_playback(device_id=device_id)
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Paused playback on Spotify.{Style.RESET_ALL}"
            }
        except Exception as e:
            print(f"Error pausing Spotify: {e}")
            return {
                "success": False,
                "error": f"Sorry, I had trouble pausing Spotify: {e}"
            }
    
    def resume_playback(self):
        """Resume Spotify playback"""
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            sp.start_playback(device_id=device_id)
            
            # Get info about what's now playing
            current_track_info = self.get_currently_playing(sp)
            
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Resumed playback on Spotify.{Style.RESET_ALL}",
                "current_track": current_track_info
            }
        except Exception as e:
            print(f"Error resuming Spotify: {e}")
            return {
                "success": False,
                "error": f"Sorry, I had trouble resuming Spotify: {e}"
            }
    
    def next_track(self):
        """Skip to the next track"""
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            sp.next_track(device_id=device_id)
            
            # Get info about what's now playing
            current_track_info = self.get_currently_playing(sp)
            
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Skipped to next track.{Style.RESET_ALL}",
                "current_track": current_track_info
            }
        except Exception as e:
            print(f"Error skipping to next track: {e}")
            return {
                "success": False,
                "error": f"Sorry, I had trouble skipping to the next track: {e}"
            }
    
    def previous_track(self):
        """Skip to the previous track"""
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            sp.previous_track(device_id=device_id)
            
            # Get info about what's now playing
            current_track_info = self.get_currently_playing(sp)
            
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Skipped to previous track.{Style.RESET_ALL}",
                "current_track": current_track_info
            }
        except Exception as e:
            print(f"Error going to previous track: {e}")
            return {
                "success": False,
                "error": f"Sorry, I had trouble going to the previous track: {e}"
            }
    
    def set_volume(self, volume_percent):
        """Set Spotify volume to a specific percentage"""
        # Convert string percentage to integer if needed
        try:
            volume_level = int(volume_percent)
            # Ensure volume is within valid range (0-100)
            volume_level = max(0, min(100, volume_level))
        except ValueError:
            return {
                "success": False,
                "error": f"Sorry, I couldn't understand that volume level. Please specify a number between 0 and 100."
            }
        
        try:
            sp = self._get_spotify_client()
            device_id, error = self._ensure_active_device(sp)
            
            if error:
                return {"error": error}
            
            # Set volume
            sp.volume(volume_level, device_id=device_id)
            
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Set Spotify volume to{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTGREEN_EX}{volume_level}{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}percent."
            }
        except Exception as e:
            print(f"Error setting Spotify volume: {e}")
            return {
                "success": False,
                "error": f"Sorry, I had trouble setting the volume: {e}"
            }
    
    def close_spotify(self):
        """Close Spotify"""
        try:
            import sys
            import subprocess
            
            platform = sys.platform
            
            if platform == "win32":
                subprocess.call("taskkill /F /IM spotify.exe", shell=True)
            elif platform == "darwin":  # macOS
                subprocess.call(["killall", "Spotify"])
            elif platform.startswith("linux"):
                subprocess.call(["killall", "spotify"])
            else:
                return {
                    "success": False,
                    "error": "Sorry, Spotify control is not supported on this platform."
                }
                
            return {
                "success": True,
                "message": "Closed Spotify."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Sorry, I had trouble closing Spotify: {e}"
            }
            
    def control_system_volume(self, action):
        """Control system volume"""
        try:               
            if action == "volume_up":
                # Increase system volume by approximately 20%
                try:
                    # Try using Windows API directly
                    from ctypes import windll
                    for _ in range(10):
                        windll.user32.keybd_event(0xAF, 0, 0, 0)  # key down (VK_VOLUME_UP = 0xAF)
                        windll.user32.keybd_event(0xAF, 0, 2, 0)  # key up
                        time.sleep(0.05)  # Small delay between presses
                    return {
                        "success": True,
                        "message": f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}Increased volume by about 20 percent.{Style.RESET_ALL}"
                    }
                except Exception as e:
                    print(f"Error using direct volume controls: {e}")
                    # Fallback to PowerShell
                    for _ in range(10):
                        subprocess.run('powershell -Command "(New-Object -com wscript.shell).SendKeys([char]175)"', shell=True)
                        time.sleep(0.05)
                    return {
                        "success": True,
                        "message": f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}Increased volume by about 20 percent.{Style.RESET_ALL}"
                    }
                
            elif action == "volume_down":
                # Decrease system volume by approximately 20%
                try:
                    # Try using Windows API directly
                    from ctypes import windll
                    for _ in range(10):
                        windll.user32.keybd_event(0xAE, 0, 0, 0)  # key down (VK_VOLUME_DOWN = 0xAE)
                        windll.user32.keybd_event(0xAE, 0, 2, 0)  # key up
                        time.sleep(0.05)  # Small delay between presses
                    return {
                        "success": True,
                        "message": f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}Decreased volume by about 20 percent.{Style.RESET_ALL}"
                    }
                except Exception as e:
                    print(f"Error using direct volume controls: {e}")
                    # Fallback to PowerShell
                    for _ in range(10):
                        subprocess.run('powershell -Command "(New-Object -com wscript.shell).SendKeys([char]174)"', shell=True)
                        time.sleep(0.05)
                    return {
                        "success": True,
                        "message": f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}Decreased volume by about 20 percent.{Style.RESET_ALL}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unknown volume control action: {action}"
                }
                
        except Exception as e:
            print(f"Error controlling system volume: {e}")
            return {
                "success": False,
                "error": f"I had trouble controlling the system volume: {e}"
            }