import requests
from datetime import datetime, timedelta
from difflib import get_close_matches

class WeatherSkill:
    def __init__(self, api_key):
        """Initialize the weather skill with API key"""
        self.api_key = api_key
    
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
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_location}&appid={self.api_key}&units=metric"
            response = requests.get(weather_url)
            
            if response.status_code == 200:
                weather_data = response.json()
                
                # Format the weather data
                city_name = weather_data['name']
                country = weather_data['sys']['country']
                temp = (weather_data['main']['temp'])
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
                
                # Create a summary for speech
                speech_summary = f"It's currently {temp}°C with {description} in {city_name}"
                
                # Return both detailed info and speech summary
                return {
                    "detailed_info": weather_info,
                    "speech_summary": speech_summary
                }
            else:
                error_info = f"Couldn't get weather: {response.status_code} - {response.reason}"
                return {"error": error_info}
                    
        except Exception as e:
            error_info = f"Error getting weather: {e}"
            return {"error": error_info}

    def get_weather_forecast(self, location):
        """Get weather forecast for a location"""
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
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={encoded_location}&appid={self.api_key}&units=metric"
            response = requests.get(forecast_url)
            
            if response.status_code == 200:
                forecast_data = response.json()
                
                # Format the forecast
                city_name = forecast_data['city']['name']
                forecast_text = f"Weather forecast for {city_name}:\\n"
                
                # Track unique days and their forecast info
                day_forecast_data = {}
                day_forecasts = {}
                today = datetime.now().strftime("%Y-%m-%d")
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                # First pass: collect all forecasts by day
                for forecast in forecast_data['list']:
                    # Parse the date
                    forecast_date = datetime.fromtimestamp(forecast['dt'])
                    forecast_day = forecast_date.strftime("%Y-%m-%d")
                    
                    # Only collect data for the next 3 days
                    if forecast_day not in day_forecast_data and len(day_forecast_data) < 3:
                        day_forecast_data[forecast_day] = {
                            'descriptions': [],
                            'temp_mins': [],
                            'temp_maxs': []
                        }
                    
                    if forecast_day in day_forecast_data:
                        # Add this forecast data to the day's collections
                        day_forecast_data[forecast_day]['descriptions'].append(forecast['weather'][0]['description'])
                        day_forecast_data[forecast_day]['temp_mins'].append((forecast['main']['temp_min']))
                        day_forecast_data[forecast_day]['temp_maxs'].append((forecast['main']['temp_max']))
                
                # Process each day's forecasts
                for forecast_day, data in day_forecast_data.items():
                    # Get the most common description (mode)
                    descriptions = data['descriptions']
                    description = max(set(descriptions), key=descriptions.count)
                    
                    # Find actual min and max temps
                    temp_min = min(data['temp_mins'])
                    temp_max = max(data['temp_maxs'])
                    
                    # Set the day name
                    if forecast_day == today:
                        day_name = "Today"
                    elif forecast_day == tomorrow:
                        day_name = "Tomorrow"
                    else:
                        day_name = datetime.strptime(forecast_day, "%Y-%m-%d").strftime("%A")
                    
                    # Store the forecast info
                    day_forecasts[day_name] = {
                        'description': description,
                        'high': temp_max,
                        'low': temp_min
                    }
                    
                    # Add to the text output
                    forecast_text += f"{day_name}: {description} with a high of {temp_max}°C and a low of {temp_min}°C\n"
                
                # Prepare speech summary
                speech_intro = f"Here's the forecast for {city_name}"
                day_summaries = []
                for day_name, forecast_info in day_forecasts.items():
                    day_summaries.append(f"{day_name}: {forecast_info['description']} with a high of {forecast_info['high']}°C and a low of {forecast_info['low']}°C")
                
                return {
                    "detailed_info": forecast_text,
                    "speech_intro": speech_intro, 
                    "day_summaries": day_summaries
                }
            else:
                error_info = f"Couldn't get forecast: {response.status_code} - {response.reason}"
                return {"error": error_info}
                    
        except Exception as e:
            error_info = f"Error getting forecast: {e}"
            return {"error": error_info}

    def get_wind_direction(self, degrees):
        """Convert wind degrees to cardinal direction"""
        directions = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest", "north"]
        index = round(degrees / 45)
        return directions[index]