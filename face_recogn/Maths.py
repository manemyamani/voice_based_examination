import sympy as sp
from gtts import gTTS
import IPython.display as display

# Define symbols
x, y = sp.symbols('x y')

# Define mathematical expression
expr = sp.Eq(x**2 + y**3, 5)  # x² + y³ = 5

# Convert to readable text
spoken_text = sp.pretty(expr, use_unicode=False)

# Convert text to speech
tts = gTTS(spoken_text, lang="en")
tts.save("math_speech.mp3")

# Play the speech in Colab
display.Audio("math_speech.mp3", autoplay=True)

print("🔊 Speaking:", spoken_text)
