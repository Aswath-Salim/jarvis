import speech_recognition as sr
import pyttsx3
import requests
import wikipedia
import datetime
import pyautogui
import webbrowser
from googletrans import Translator
import time
import json # Import json for parsing API responses

# Initialize Translator
translator = Translator()

# Initialize pyttsx3 engine once for efficiency
# This avoids re-initializing the engine for every speak call, which can cause delays.
try:
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
except Exception as e:
    print(f"Error initializing TTS engine: {e}")
    engine = None # Set engine to None if initialization fails

# Speak function
from gtts import gTTS
import pygame
import time
import os
import re

def clean_text(text):
    return re.sub(r'[^A-Za-z0-9\s]', '', text)

def speak(text):
    print("Jarvis:", text)
    try:
        cleaned = clean_text(text)
        tts = gTTS(text=cleaned, lang='en', tld='co.uk')  # UK voice for smoother tone
        filename = "temp_voice.mp3"
        tts.save(filename)

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.3)

        pygame.mixer.music.unload()
        os.remove(filename)

    except Exception as e:
        print(f"Voice error: {e}")

# Listen to mic
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # Corrected: Removed space in adjust_for_ambient_noise
        r.adjust_for_ambient_noise(source, duration=0.5) # Adjust for ambient noise
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=7)
            print("Recognizing...")
            query = r.recognize_google(audio)
            print("You:", query)
            return query
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Please try again.")
            return ""
        except sr.UnknownValueError:
            speak("Sorry, I couldn't understand what you said.")
            return ""
        except sr.RequestError as e:
            speak(f"Could not request results from Google Speech Recognition service; {e}")
            return ""
        except Exception as e:
            print(f"An unexpected error occurred during listening: {e}")
            return ""

# Call Gemini API
def get_gemini_response(prompt: str) -> str:
    # IMPORTANT: Replace "YOUR_GEMINI_API_KEY_HERE" with your actual Gemini API key.
    # You can get one from Google AI Studio: https://aistudio.google.com/
    apiKey = "AIzaSyDes-ofdRaHAw_0T3McmDk4Vxag39qvJhE"
    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"

    chatHistory = []
    # Corrected: Use .append() for Python lists instead of .push()
    chatHistory.append({ "role": "user", "parts": [{ "text": prompt }] })

    payload = {
        "contents": chatHistory
    }

    try:
        # Make the fetch call using requests library for Python
        response = requests.post(apiUrl, headers={'Content-Type': 'application/json'}, json=payload, timeout=60)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)

        result = response.json()

        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return text
        else:
            print(f"Gemini API response structure unexpected: {result}")
            return "I received an unexpected response from the AI."
    except requests.exceptions.Timeout:
        return "The AI took too long to respond. Please try again."
    except requests.exceptions.ConnectionError:
        return "I couldn't connect to the AI service. Please check your internet connection."
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return f"An HTTP error occurred while contacting the AI: {http_err}. Please check the API key and service status."
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from response: {response.text}")
        return "I received an unreadable response from the AI."
    except Exception as e:
        print(f"An unexpected error occurred while getting Gemini response: {e}")
        return "I encountered an error while processing your request with the AI."


# Handle commands
def process_command(command):
    command = command.lower()

    if "time" in command:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        speak(f"The time is {now}")

    elif "open" in command:
        if "chrome" in command:
            speak("Opening Chrome")
            pyautogui.press("win")
            pyautogui.write("chrome")
            pyautogui.press("enter")
        elif "notepad" in command:
            speak("Opening Notepad")
            pyautogui.press("win")
            pyautogui.write("notepad")
            pyautogui.press("enter")
        elif "youtube" in command:
            webbrowser.open("https://youtube.com")
            speak("Opening YouTube")
        else:
            speak("I can open Chrome, Notepad, or YouTube. What would you like to open?")

    elif "weather" in command:
        city_match = None
        # Simple parsing for "weather in <city>"
        if "weather in" in command:
            city_match = command.split("weather in", 1)[1].strip()
        elif "weather of" in command:
            city_match = command.split("weather of", 1)[1].strip()

        if city_match:
            city = city_match.replace("the", "").strip()
            # IMPORTANT: The 'demo' key for weatherapi.com is for demonstration purposes only and will not work for real requests.
            # You need to sign up at weatherapi.com and get a free API key.
            weather_key = "YOUR_WEATHER_API_KEY_HERE" # <<< REPLACE WITH YOUR ACTUAL WEATHERAPI.COM KEY
            if weather_key == "YOUR_WEATHER_API_KEY_HERE":
                speak("Please replace 'YOUR_WEATHER_API_KEY_HERE' with a valid API key from weatherapi.com to get weather information.")
                return

            url = f"http://api.weatherapi.com/v1/current.json?key={weather_key}&q={city}"
            try:
                res = requests.get(url, timeout=10)
                res.raise_for_status() # Raise an exception for HTTP errors
                data = res.json()
                temp = data["current"]["temp_c"]
                cond = data["current"]["condition"]["text"]
                speak(f"The temperature in {city} is {temp}°C with {cond}.")
            except requests.exceptions.RequestException as e:
                speak(f"Could not fetch weather for {city}. Error: {e}")
            except KeyError:
                speak(f"Could not find weather information for {city}. Please ensure the city name is correct.")
        else:
            speak("Please specify the city for which you want the weather. For example, 'weather in London'.")

    elif "who is" in command or "what is" in command:
        topic = command.replace("who is", "").replace("what is", "").strip()
        if topic:
            try:
                speak(f"Searching Wikipedia for {topic}...")
                summary = wikipedia.summary(topic, sentences=2)
                speak(summary)
            except wikipedia.exceptions.DisambiguationError as e:
                speak(f"There are multiple results for {topic}. Can you be more specific? Options include: {', '.join(e.options[:3])}.")
            except wikipedia.exceptions.PageError:
                speak(f"Sorry, I couldn't find any information on Wikipedia about {topic}.")
            except Exception as e:
                speak(f"An error occurred while searching Wikipedia: {e}")
        else:
            speak("Please tell me who or what you want to know about.")

    elif "translate" in command:
        parts = command.split("to")
        if len(parts) == 2:
            text_to_translate = parts[0].replace("translate", "").strip()
            dest_language = parts[1].strip()
            if text_to_translate and dest_language:
                try:
                    speak(f"Translating '{text_to_translate}' to {dest_language}...")
                    translated = translator.translate(text_to_translate, dest=dest_language)
                    speak(translated.text, lang=dest_language)
                except Exception as e:
                    speak(f"Sorry, I couldn't translate that. Error: {e}. Please ensure the language is valid (e.g., 'french', 'spanish').")
            else:
                speak("Please say: translate <text> to <language>")
        else:
            speak("Please say: translate <text> to <language>")

    elif "exit" in command or "stop" in command or "quit" in command:
        speak("Goodbye! Have a great day.")
        exit()

    else:
        # Use Gemini for general queries
        speak("Let me think about that.")
        response = get_gemini_response(command)
        speak(response)

# Main loop
if __name__ == "__main__":
    if engine is None:
        print("TTS engine failed to initialize. Exiting.")
        exit()

    speak("Hello, I am Jarvis. How can I help you?")
    while True:
        command = listen()
        if command: # Only process if a command was recognized
            process_command(command)
