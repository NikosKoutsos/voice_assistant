#!/usr/bin/env python3
"""
Voice Assistant - Main Entry Point
---------------------------------
A modular voice assistant that responds to voice commands
and provides various services like weather, music control, and web searches.

Usage:
    python main.py           # Shows startup menu
    python main.py voice     # Starts directly in voice mode
    python main.py text      # Starts directly in text mode
"""

import sys
import json
import os
from voice_assistant import VoiceAssistant
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

def load_config():
    """Load configuration from config.json if available"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as config_file:
                return json.load(config_file)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration.")
    
    # Return None to use default configuration in VoiceAssistant class
    return None

def main():
    """Main entry point function"""
    
    # Load configuration
    config = load_config()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        assistant = VoiceAssistant(config)
        
        if mode == "voice":
            assistant.start_voice_mode()
        elif mode == "text":
            assistant.start_text_mode()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python main.py [voice|text]")
    else:
        # No command line arguments, show menu
        print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Which assistant would you like to start?{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}1.{Style.RESET_ALL} {Fore.CYAN}Voice Assistant :{Style.RESET_ALL} {Style.DIM}{Fore.CYAN}Wake word + speech recognition{Style.RESET_ALL}")
        print(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}2.{Style.RESET_ALL} {Fore.GREEN}Text Assistant :{Style.RESET_ALL} {Style.DIM}{Fore.GREEN}Type commands{Style.RESET_ALL}")
        
        try:
            choice = input(f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Enter 1 or 2: {Style.RESET_ALL}")
            assistant = VoiceAssistant(config)
            
            if choice == "1":
                assistant.start_voice_mode()
            else:
                assistant.start_text_mode()
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()