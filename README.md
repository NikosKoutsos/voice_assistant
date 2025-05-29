# Voice Assistant

A comprehensive Python-based voice assistant that provides intelligent voice control for various system functions and services. The assistant features wake word detection, speech recognition, text-to-speech capabilities, and integration with multiple APIs for weather, music control, web search, and more.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## 🌟 Features

### Core Functionality
- **Wake Word Detection**: Responds to "Hey Google", "Jarvis", or "Computer"
- **Speech Recognition**: Google Speech Recognition API integration
- **Text-to-Speech**: Natural voice responses with customizable voice settings
- **Dual Mode Operation**: Voice mode with wake word detection or text input mode
- **Colorized Output**: Beautiful terminal interface with color-coded responses

### Skills & Integrations

#### 🎵 Spotify Control
- Play songs, playlists, and albums
- Control playback (pause, resume, next, previous)
- Volume control (Spotify and system volume)
- Device management and switching
- Built-in playlist recognition for popular playlists

The spotify playlist that exist in the spotify_skill.py are entirely personal. Users are happy to attain the IDs of their favorite playlists, add them to their .env file and modify the
code for their own personal experience.

#### 🌤️ Weather Services
- Current weather conditions for any location
- 5-day weather forecasts
- Detailed weather information with temperature, humidity, wind speed
- Automatic location matching with fuzzy search

#### 🌙 Astronomy Features
- Current moon phase information
- Next full moon date calculations
- Detailed astronomical data

#### 🔍 Web & Information
- Web search functionality
- Wikipedia summaries and lookups
- Website and application launching
- Smart URL recognition

#### 🛠️ System Utilities
- Internet speed testing
- Time and date queries
- Find my phone functionality
- Reminder system
- Application control

## 📁 Project Structure

```
voice_assistant/
├── main.py                    # Main entry point
├── voice_assistant.py         # Core assistant class
├── skills/                    # Skill modules
│   ├── spotify_skill.py       # Spotify integration
│   ├── weather_skill.py       # Weather services
│   ├── web_skill.py          # Web search and navigation
│   └── moonphase_skill.py    # Moon phase calculations
├── utils/                     # Utility modules
│   ├── wake_word_detector.py # Wake word detection
│   └── common.py             # Common utilities
├── .env                      # Environment variables (not tracked)
├── .gitignore               # Git ignore configuration
└── README.md                # This documentation
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Windows operating system (for system-specific features)
- Microphone and speakers/headphones
- Internet connection for API services

### Required Python Packages

```bash
pip install speech-recognition
pip install pyttsx3
pip install spotipy
pip install requests
pip install python-dotenv
pip install colorama
pip install speedtest-cli
pip install wikipedia-api
pip install pvporcupine
pip install pyaudio
```

### System Dependencies

#### For speech recognition:
```bash
# Windows users may need to install PyAudio separately
pip install pyaudio
```

#### For wake word detection:
- Picovoice Porcupine (included in pvporcupine package)

### Environment Setup

1. Clone or download the project to your local machine
2. Create a `.env` file in the project root directory
3. Add your API keys and configuration:

```env
# Required API Keys
WEATHER_API_KEY=your_openweathermap_api_key
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
WAKE_WORD_ACCESS_KEY=your_picovoice_access_key

# Optional API Keys
ASTRONOMY_API_ID=your_astronomy_api_id
ASTRONOMY_API_SECRET=your_astronomy_api_secret
```

## 🔧 Configuration

### API Key Setup

#### Weather API (OpenWeatherMap)
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key
4. Add to `.env` file as `WEATHER_API_KEY`

#### Spotify API
1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Note the Client ID and Client Secret
4. Set redirect URI to `http://localhost:8888/callback`
5. Add credentials to `.env` file

#### Wake Word Detection (Picovoice)
1. Visit [Picovoice Console](https://console.picovoice.ai/)
2. Sign up for a free account
3. Generate an access key
4. Add to `.env` file as `WAKE_WORD_ACCESS_KEY`

#### Astronomy API (Optional)
1. Visit [Astronomy API](https://astronomyapi.com/)
2. Sign up for an account
3. Get your application ID and secret
4. Add to `.env` file

### Voice Configuration

The assistant automatically selects the best available voice. You can modify voice settings in `voice_assistant.py`:

```python
# Configure voice properties
voices = self.engine.getProperty('voices')
self.engine.setProperty('rate', 180)  # Speech rate (words per minute)
```

## 🎯 Usage

### Starting the Assistant

#### Option 1: Interactive Menu
```bash
python main.py
```
This displays a menu to choose between voice or text mode.

#### Option 2: Direct Mode Launch
```bash
# Start in voice mode directly
python main.py voice

# Start in text mode directly
python main.py text
```

### Voice Commands

#### Weather Commands
- "What's the weather?"
- "Weather in London"
- "Get me the forecast"
- "Forecast for New York"

#### Spotify Commands
- "Play Bohemian Rhapsody on Spotify"
- "Play my liked songs"
- "Pause Spotify"
- "Resume music"
- "Next song"
- "Previous track"
- "Set volume to 50 percent"
- "Volume up" / "Volume down"

#### Information Commands
- "What time is it?"
- "What's today's date?"
- "Search for Python programming"
- "Tell me about Albert Einstein"
- "What's the moon phase?"
- "When's the next full moon?"

#### System Commands
- "Test my internet speed"
- "Find my phone"
- "Open Chrome"
- "Go to YouTube"
- "Remind me to call mom at 3 PM"

#### Navigation Commands
- "Help" - Shows available commands
- "Exit" / "Quit" / "Goodbye" - Stops the assistant

### Text Mode

In text mode, simply type any of the voice commands above and press Enter. The assistant will process the command and respond accordingly.

## 🏗️ Architecture

### Core Components

#### VoiceAssistant Class (`voice_assistant.py`)
The main coordinator that:
- Manages speech recognition and text-to-speech
- Handles command pattern matching
- Coordinates between different skill modules
- Manages application state and lifecycle

#### Skill Modules (`skills/`)
Modular components for specific functionality:
- **SpotifySkill**: Spotify Web API integration and music control
- **WeatherSkill**: Weather data retrieval and formatting
- **WebSkill**: Web search and application launching
- **MoonPhaseSkill**: Astronomical calculations and data

#### Utility Modules (`utils/`)
Supporting functionality:
- **WakeWordDetector**: Picovoice integration for wake word detection
- **Common**: Time utilities, system operations, and shared functions

### Command Processing Flow

1. **Wake Word Detection**: Listens for wake words using Picovoice Porcupine
2. **Speech Recognition**: Converts voice to text using Google Speech Recognition
3. **Pattern Matching**: Uses regex patterns to identify command intent
4. **Skill Delegation**: Routes commands to appropriate skill modules
5. **Response Generation**: Formats and delivers responses via text-to-speech

### Data Flow

```
User Voice Input → Wake Word Detection → Speech Recognition → 
Pattern Matching → Skill Processing → API Calls → Response Generation → 
Text-to-Speech Output
```

## 🔍 API Documentation

### VoiceAssistant Class

#### Main Methods

```python
def __init__(self, config=None)
```
Initialize the assistant with optional configuration.

```python
def start_voice_mode(self)
```
Start the assistant in voice mode with wake word detection.

```python
def start_text_mode(self)
```
Start the assistant in text input mode.

```python
def process_command(self, text)
```
Process a text command and return appropriate response.

```python
def speak(self, text, text_color=None)
```
Convert text to speech with optional color formatting.

### Skill Classes

#### SpotifySkill

```python
def play_song(self, song_name)
```
Search for and play a specific song.

```python
def play_playlist(self, playlist_name)
```
Play a named playlist.

```python
def pause_playback(self)
```
Pause current playback.

```python
def resume_playback(self)
```
Resume paused playback.

#### WeatherSkill

```python
def get_weather(self, location)
```
Get current weather for specified location.

```python
def get_weather_forecast(self, location)
```
Get 5-day forecast for specified location.

#### WebSkill

```python
def search_web(self, query)
```
Perform web search and open results.

```python
def open_website(self, website_name)
```
Open specified website in default browser.

```python
def get_wikipedia_summary(self, query)
```
Get Wikipedia summary for a topic.

## 🛠️ Troubleshooting

### Common Issues

#### Speech Recognition Problems
- **Issue**: "Sorry, my speech service is down"
- **Solution**: Check internet connection; Google Speech Recognition requires internet

#### Wake Word Not Detected
- **Issue**: Wake words not triggering the assistant
- **Solutions**: 
  - Check microphone permissions
  - Verify Picovoice access key
  - Adjust sensitivity settings
  - Ensure clear pronunciation

#### Spotify Integration Issues
- **Issue**: "No active Spotify devices found"
- **Solutions**:
  - Open Spotify application
  - Start playing any song to activate device
  - Check Spotify API credentials
  - Verify redirect URI configuration

#### Import Errors
- **Issue**: Module import failures
- **Solutions**:
  - Install missing packages: `pip install -r requirements.txt`
  - Check Python version (3.8+ required)
  - Verify virtual environment activation

### Debug Mode

Enable debug output by modifying the logging level in the main files:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Optimization

#### For Faster Response Times:
- Use local speech recognition (consider Vosk for offline capability)
- Cache API responses where appropriate
- Optimize wake word sensitivity settings

#### For Better Accuracy:
- Improve microphone quality
- Reduce background noise
- Adjust speech recognition energy threshold

## 🔮 Future Enhancements


### Extension Points
- Plugin architecture for custom skills
- Configurable command patterns
- Multiple TTS engine support
- Cloud synchronization
- Mobile companion app

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is currently unlicensed. Please refer to the repository owner for licensing information.

## 🙏 Acknowledgments

- [Picovoice](https://picovoice.ai/) for wake word detection
- [Google Speech Recognition](https://cloud.google.com/speech-to-text) for speech processing
- [Spotify Web API](https://developer.spotify.com/documentation/web-api/) for music integration
- [OpenWeatherMap](https://openweathermap.org/) for weather data
- [Wikipedia API](https://wikipedia.org/) for information lookup

## 📞 Support

For support, questions, or feature requests:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review the API documentation

---

**Note**: This voice assistant is designed for personal use and requires various API keys for full functionality. Always respect rate limits and terms of service for external APIs.
