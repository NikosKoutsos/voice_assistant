import re
import webbrowser
import requests
import subprocess
import sys
import wikipedia
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=False)

class TimeUtility:
    """Handles time and date related functions"""
    
    @staticmethod
    def get_time():
        """Get the current time in a spoken format"""
        current_time = datetime.now().strftime("%I:%M %p")
        return f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}The current time is {Style.BRIGHT}{Fore.CYAN}{current_time}.{Style.RESET_ALL}"
    
    @staticmethod
    def get_date():
        """Get the current date in a spoken format"""
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Today is {Style.BRIGHT}{Fore.CYAN}{current_date}.{Style.RESET_ALL}"
    
    @staticmethod
    def set_reminder(reminder_text, reminder_time):
        """Set a simple reminder"""
        # This would typically integrate with a scheduling system
        # For demonstration, we'll just log it
        print(f"REMINDER SET: {reminder_text} at {reminder_time}")
        
        return f"I've set a reminder for '{reminder_text}' at {reminder_time}."


class SystemUtility:
    """Handles system-related functions like speed tests and phone finding"""
    
    @staticmethod
    def run_speedtest():
        """Run an internet speed test"""
        import speedtest
        
        try:
            st = speedtest.Speedtest()
            print(f"{Fore.CYAN}Finding the best server...")
            st.get_best_server()
            
            print("Testing download speed...")
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            
            print(f"Testing upload speed...{Style.RESET_ALL}")
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            
            ping = st.results.ping
            
            result = f"{Fore.YELLOW}Speed test results: Download speed:{Style.RESET_ALL} {Fore.CYAN}{download_speed:.2f}{Style.RESET_ALL} {Fore.YELLOW}Mbps, Upload speed:{Style.RESET_ALL} {Fore.CYAN}{upload_speed:.2f}{Style.RESET_ALL} {Fore.YELLOW}Mbps, Ping:{Style.RESET_ALL} {Fore.CYAN}{ping}{Style.RESET_ALL} {Fore.YELLOW}ms{Style.RESET_ALL}"
            
            speech_text = result
            
            print(result)
            return {
                "speech_text": speech_text
            }
        except Exception as e:
            print(f"Error running speed test: {e}")
            return {
                "error": f"Sorry, I couldn't perform the speed test: {e}"
            }
            
    @staticmethod
    def find_my_phone():
        """Open Google's Find My Device service to help locate an Android phone"""
        try:
            # Open Google's Find My Device service
            webbrowser.open("https://android.com/find")
            
            # Provide clear instructions
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}I've opened Google Find My Device. Once the page loads, click on your device and select Play Sound to make it ring at full volume.{Style.RESET_ALL}"
            }
                
        except Exception as e:
            print(f"Error opening Find My Device: {e}")
            return {
                "success": False,
                "error": f"I encountered an error while trying to open Find My Device: {e}"
            }