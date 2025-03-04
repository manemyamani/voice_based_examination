import vosk
import sys
import json
import pyaudio

# Load Vosk model (Change "vosk-model-small-en-us-0.15" to your model folder)
model = vosk.Model("vosk-model-small-en-us-0.15")

# Initialize recognizer
recognizer = vosk.KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

print("Listening... Speak now.")

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        print("Recognized Text:", result["text"])  # This text can be stored in your DB
