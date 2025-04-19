import speech_recognition as sr

def speech_to_text():
    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Use the default microphone as the audio source
    with sr.Microphone() as source:
        print("Please speak something...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = recognizer.listen(source)  # Listen for the first phrase

    try:
        # Recognize speech using Google Speech Recognition
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print(f"Text: {text}")

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
    except sr.RequestError:
        print("Sorry, the service is unavailable. Please try again later.")

if __name__ == "__main__":
    speech_to_text()
