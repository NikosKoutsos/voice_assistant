import webbrowser
import requests
import re
import sys
import subprocess
import wikipedia
from colorama import init, Fore, Style
import webbrowser
import urllib.parse


init(autoreset=True)


class WebSkill:
    """Handles web-related operations like search, website opening, and Wikipedia lookups"""
    
    @staticmethod
    def search_web(query):
        """Search the web for a query using default browser"""
        try:
            # URL encode the query
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(search_url)
            
            return {
                "success": True,
                "message": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}I've opened a web search for {Fore.CYAN}{query}{Fore.LIGHTYELLOW_EX}.{Style.RESET_ALL}"
            }
        except Exception as e:
            print(f"Error searching the web: {e}")
            return {
                "success": False,
                "error": f"I encountered an error while searching the web: {e}"
            }
    
    @staticmethod
    def open_website(website_name):
        """Open a website with robust handling of different inputs"""
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
            "claude.ai": "https://claude.ai",
            "crunchyroll.com": "https://www.crunchyroll.com/"
        }
        
        website_name = website_name.lower().strip()
        
        # Check if it's a known website
        if website_name in websites:
            webbrowser.open(websites[website_name])
            return f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}Opening {Fore.CYAN}{website_name}{Fore.LIGHTYELLOW_EX} now.{Style.RESET_ALL}"
        
        # Check if it's a URL with http/https
        if website_name.startswith(("http://", "https://")):
            webbrowser.open(website_name)
            return f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}Opening {Fore.CYAN}{website_name}{Fore.LIGHTYELLOW_EX} now.{Style.RESET_ALL}"
        
        # Check if it ends with a common TLD
        if re.search(r"\.(com|org|net|edu|gov|io|tv)$", website_name):
            webbrowser.open(f"https://{website_name}")
            return f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}Opening {Fore.CYAN}{website_name}{Fore.LIGHTYELLOW_EX} now.{Style.RESET_ALL}"
        
        # Default - Try adding www. and .com
        try:
            webbrowser.open(f"https://www.{website_name}.com")
            return f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}Opening {Fore.CYAN}{website_name}{Fore.LIGHTYELLOW_EX} now.{Style.RESET_ALL}"
        except:
            return f"Sorry, I couldn't open the website {website_name}."
    
    @staticmethod
    def open_application(app_name):
        """Open an application with platform awareness"""
        app_name = app_name.strip().lower()
        
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
            
            return f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}Opening{Style.RESET_ALL} {Fore.CYAN}{app_name}{Style.RESET_ALL}{Fore.LIGHTYELLOW_EX} now.{Style.RESET_ALL}"
            
        except Exception as e:
            return f"Sorry, I couldn't open {app_name}: {e}"
    
    @staticmethod
    def get_wikipedia_summary(query):
        """Get a summary from Wikipedia with improved handling for disambiguation pages"""
        # If the query starts with 'what is' or similar, extract the core concept
        core_query = query.lower()
        prefixes = ['what is', 'what are', 'who is', 'who was', 'tell me about']
        for prefix in prefixes:
            if core_query.startswith(prefix):
                core_query = core_query[len(prefix):].strip()
                break
        
        # Try direct search with the original query first
        try:
            # First try a direct search
            summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
            
            # Clean up the summary
            summary = summary.replace("( listen)", "").replace(" ", " ")
            
            return {
                "summary": summary,
                "speech_text": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}According to Wikipedia: {Style.BRIGHT}{Fore.CYAN}{summary[:300]}...{Style.RESET_ALL}"
            }

        except wikipedia.exceptions.DisambiguationError as e:
            # Get the options from the disambiguation page
            options = e.options
            
            if not options:
                return {
                    "error": f"Sorry, Wikipedia has multiple interpretations for '{query}' but I couldn't retrieve them."
                }
            
            # Smarter option selection strategy:
            # If we're asking about a general concept like "dream", prioritize:
            # 1. Exact match to core query without any qualifiers
            # 2. Options that contain "psychology", "concept", or other general terms
            # 3. Options without parentheses (often the general concept)
            # 4. Only after that, fall back to standard matches
            
            exact_match = None
            general_concept_match = None
            
            # First pass - look for the exact concept or a general concept version
            concept_keywords = ["concept", "psychology", "meaning", "general", "phenomenon"]
            
            # Look for exact match without parenthetical qualifier
            for option in options:
                if option.lower() == core_query.lower():
                    exact_match = option
                    break
                    
            # If no exact match, look for options with general concept keywords
            if not exact_match:
                for option in options:
                    option_lower = option.lower()
                    # Check if any concept keyword is in the option
                    if any(keyword in option_lower for keyword in concept_keywords):
                        general_concept_match = option
                        break
            
            # If still no match, look for an option that doesn't have parentheses (often the general concept)
            if not exact_match and not general_concept_match:
                for option in options:
                    if "(" not in option and option.lower() != core_query.lower() + "s":  # Avoid plural form as separate entry
                        general_concept_match = option
                        break
            
            # If still no match, try searching the Wikipedia database directly
            if not exact_match and not general_concept_match:
                # Try searching Wikipedia for the core concept + "psychology" or "concept"
                search_results = wikipedia.search(core_query + " concept", results=3)
                if not search_results:
                    search_results = wikipedia.search(core_query + " psychology", results=3)
                
                if search_results:
                    for result in search_results:
                        try:
                            summary = wikipedia.summary(result, sentences=3, auto_suggest=False)
                            print(f"Selected search result: {result}")
                            summary = summary.replace("( listen)", "").replace(" ", " ")
                            
                            return {
                                "summary": summary,
                                "speech_text": f"According to Wikipedia, {result} is: {summary[:300]}..."
                            }
                        except Exception:
                            continue
            
            # Use our best match
            selected_option = exact_match or general_concept_match or options[0]
            
            try:
                print(f"Selected Wikipedia option: {selected_option}")
                summary = wikipedia.summary(selected_option, sentences=3, auto_suggest=False)
                summary = summary.replace("( listen)", "").replace(" ", " ")
                
                print(f"Wikipedia summary for {selected_option}:\n{summary}")
                
                return {
                    "summary": summary,
                    "speech_text": f"According to Wikipedia, {selected_option} is: {summary[:300]}..."
                }
            except Exception as e2:
                print(f"Error getting summary for selected option: {e2}")
                
                # Last resort - try a general search for the core concept
                try:
                    print(f"Trying general search for: {core_query}")
                    search_results = wikipedia.search(core_query, results=5)
                    
                    if search_results:
                        # Try each result until one works
                        for result in search_results:
                            try:
                                summary = wikipedia.summary(result, sentences=3, auto_suggest=False)
                                summary = summary.replace("( listen)", "").replace(" ", " ")
                                
                                print(f"Wikipedia summary for {result} (search result for '{query}'):\n{summary}")
                                
                                return {
                                    "summary": summary,
                                    "speech_text": f"I found this related information about {result}: {summary[:300]}..."
                                }
                            except:
                                continue
                except Exception as e3:
                    print(f"Error in general search: {e3}")
            
            # If everything fails, return the disambiguation options
            options_display = options[:5]  # First 5 options only to avoid overwhelming
            options_text = ", ".join(options_display)
            return {
                "error": f"There are multiple definitions for '{query}'. Options include: {options_text}"
            }
        except wikipedia.exceptions.PageError:
            # Try a direct search for "dream psychology" or similar for common concepts
            try:
                # For common general concepts, try specialized searches
                if core_query.lower() in ["dream", "dreams"]:
                    special_searches = ["Dream", "Dream interpretation", "Dream psychology"]
                    for special_query in special_searches:
                        try:
                            summary = wikipedia.summary(special_query, sentences=3, auto_suggest=False)
                            summary = summary.replace("( listen)", "").replace(" ", " ")
                            
                            print(f"Wikipedia summary for special search '{special_query}':\n{summary}")
                            
                            return {
                                "summary": summary,
                                "speech_text": f"According to Wikipedia, {special_query} is: {summary[:300]}..."
                            }
                        except:
                            continue
            except:
                pass
                
            # Try a general search
            search_results = wikipedia.search(query, results=5)
            
            if search_results:
                try:
                    # Try to get a summary of the first search result
                    first_result = search_results[0]
                    summary = wikipedia.summary(first_result, sentences=3, auto_suggest=False)
                    summary = summary.replace("( listen)", "").replace(" ", " ")
                    
                    print(f"Wikipedia summary for {first_result} (best match for '{query}'):\n{summary}")
                    
                    return {
                        "summary": summary,
                        "speech_text": f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}I couldn't find '{query}' exactly, but here's info on {Fore.CYAN}{first_result}{Fore.LIGHTYELLOW_EX}: {Fore.CYAN}{summary[:300]}{Fore.LIGHTYELLOW_EX}...{Style.RESET_ALL}"
                    }
                except Exception as e:
                    print(f"Error getting summary for search result: {e}")
            
            # If search also fails or finds nothing
            return {
                "error": f"Sorry, I couldn't find any Wikipedia information about '{query}'"
            }
        except Exception as e:
            print(f"Error getting Wikipedia summary: {e}")
            return {
                "error": f"Sorry, I had trouble accessing Wikipedia: {e}"
            }