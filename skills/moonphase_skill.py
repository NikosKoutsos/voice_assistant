import base64
import requests
import datetime
from datetime import datetime, timezone as dt_timezone, timedelta
from colorama import init, Fore, Style
from pytz import timezone as pytz_timezone

init(autoreset=False)

class MoonPhaseSkill:
    """Skill for retrieving the current moon phase."""
    
    def __init__(self, api_key):
        """Initialize with API key"""
        self.api_key = api_key
        self.base_url = "https://api.astronomyapi.com/api/v2/bodies/positions"
        
    def get_moon_phase(self, date=None):
        """Get the current moon phase information"""
        try:
            # Ensure the date and time are in UTC
            now_utc = datetime.now(dt_timezone.utc)
            date = date or now_utc.strftime("%Y-%m-%d")
            time = now_utc.strftime("%H:%M:%S")
            
            auth = base64.b64encode(f"{self.api_key['app_id']}:{self.api_key['app_secret']}".encode()).decode()
            
            params = {
                'latitude': 0,  # Replace with your latitude
                'longitude': 0,  # Replace with your longitude
                'elevation': 0,  # Replace with your elevation
                'from_date': date,
                'to_date': date,
                'time': time,
                'bodies': 'moon',
            }
            
            headers = {
                
                'Authorization': f'Basic {auth}'
            }
            
            response = requests.get(self.base_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()

                # Extract moon phase data correctly
                moon_data = data['data']['table']['rows'][1]['cells'][0]  # Access the moon entry
                phase_name = moon_data['extraInfo']['phase']['string']  # Correct field for phase name
                fraction = moon_data['extraInfo']['phase']['fraction']

                # Fallback logic for illumination
                if float(fraction) == 0.0:
                    if "New Moon" in phase_name:
                        illumination = 0.0
                    elif "Waxing Crescent" in phase_name:
                        illumination = 0.25
                    elif "First Quarter" in phase_name:
                        illumination = 0.5
                    elif "Waxing Gibbous" in phase_name:
                        illumination = 0.75
                    elif "Full Moon" in phase_name:
                        illumination = 1.0
                    elif "Waning Gibbous" in phase_name:
                        illumination = 0.75
                    elif "Last Quarter" in phase_name:
                        illumination = 0.5
                    elif "Waning Crescent" in phase_name:
                        illumination = 0.25
                    else:
                        illumination = 0.0
                else:
                    illumination = float(fraction)  # Convert fraction to float

                response_text = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}The current moon phase is{Style.RESET_ALL} {Fore.CYAN}{phase_name}{Style.RESET_ALL} {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}with an illumination of approximately{Style.RESET_ALL} {Fore.CYAN}{int(illumination * 100)}%.{Style.RESET_ALL}"
                detailed_info = (f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Moon Phase:{Style.RESET_ALL} {Fore.CYAN}{phase_name}{Style.RESET_ALL}\n"
                                f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}Illumination: {Style.RESET_ALL} {Fore.CYAN}{int(illumination * 100)}%{Style.RESET_ALL}\n")

                return {
                    "success": True,
                    "speech": response_text,
                    "detailed_info": detailed_info,
                    "phase": phase_name,
                    "illumination": illumination,
                    "phase_angle": None,
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.reason}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    def _get_phase_name(self, angle):
            """Get the name of the moon phase based on the angle"""
            if angle == 0:
                return "New Moon"
            elif 0 < angle < 90:
                return "Waxing Crescent"
            elif angle == 90:
                return "First Quarter"
            elif 90 < angle < 180:
                return "Waxing Gibbous"
            elif angle == 180:
                return "Full Moon"
            elif 180 < angle < 270:
                return "Waning Gibbous"
            elif angle == 270:
                return "Last Quarter"
            else:
                return "Waning Crescent"
    
    def get_next_full_moon(self):
        """Get the date of the next full moon"""
        try:
            # Adjusted list of known full moon dates for 2025
            full_moons_2025 = [
                datetime(2025, 1, 13, 22, 27, tzinfo=dt_timezone.utc),
                datetime(2025, 2, 12, 13, 53, tzinfo=dt_timezone.utc),
                datetime(2025, 3, 14, 2, 55, tzinfo=dt_timezone.utc),
                datetime(2025, 4, 13, 13, 22, tzinfo=dt_timezone.utc),  # Corrected to April 13, 2025
                datetime(2025, 5, 12, 0, 56, tzinfo=dt_timezone.utc),   # Corrected to May 12, 2025
                datetime(2025, 6, 10, 15, 2, tzinfo=dt_timezone.utc),
                datetime(2025, 7, 10, 6, 37, tzinfo=dt_timezone.utc),
                datetime(2025, 8, 8, 23, 2, tzinfo=dt_timezone.utc),
                datetime(2025, 9, 7, 15, 10, tzinfo=dt_timezone.utc),
                datetime(2025, 10, 7, 5, 48, tzinfo=dt_timezone.utc),
                datetime(2025, 11, 5, 18, 19, tzinfo=dt_timezone.utc),
                datetime(2025, 12, 5, 4, 15, tzinfo=dt_timezone.utc),
            ]

            # Get current date and time
            now_utc = datetime.now(dt_timezone.utc)

            # Find the next full moon after the current time or within the next 24 hours
            next_full_moon_date = next((fm for fm in full_moons_2025 if fm >= now_utc), None)

            if not next_full_moon_date:
                # If no future full moon is found, estimate using the last known date
                last_full_moon = full_moons_2025[-1]
                lunar_cycle = 29.53059  # Average lunar cycle in days
                next_full_moon_date = last_full_moon + timedelta(days=lunar_cycle)

            # Define Greece time zone
            GREECE_TZ = pytz_timezone("Europe/Athens")

            # Convert the next full moon date to the Greece time zone
            local_next_full_moon_date = next_full_moon_date.astimezone(GREECE_TZ)

            # Format the date in the Greece time zone
            formatted_date = local_next_full_moon_date.strftime("%A, %B %d, %Y")

            # Calculate days until the next full moon
            local_now = datetime.now(GREECE_TZ)
            days_until_next = (local_next_full_moon_date - local_now).total_seconds() / (24 * 3600)

            # Round up partial days to the next full day
            days_away = int(days_until_next) if days_until_next.is_integer() else int(days_until_next) + 1

            # Adjust the time description
            if days_away == 0:
                time_description = "today"
            elif days_away == 1:
                time_description = "tomorrow"
            else:
                time_description = f"in {days_away} days"

            response_text = f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}The next full moon will be{Style.RESET_ALL} {Fore.CYAN}{time_description}{Style.RESET_ALL}, {Style.BRIGHT}{Fore.LIGHTYELLOW_EX}on{Style.RESET_ALL} {Fore.CYAN}{formatted_date}.{Style.RESET_ALL}"

            return {
                "success": True,
                "date": formatted_date,
                "days_away": days_away,
                "speech": response_text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }