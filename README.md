# Aura Assist - Voice-Based Examination System

Aura Assist is an AI-powered voice-based examination system designed to assist blind individuals in taking assessments independently. It leverages advanced speech-to-text and text-to-speech technologies to facilitate a seamless examination process.

## Features

- **Voice-Based Interface**: Converts text-based questions into speech and records spoken answers.
- **Face Verification**: Ensures candidate authentication using OpenCV and dlib.
- **Speech-to-Text & Text-to-Speech**: Uses Wave2Vec 2.0 for speech recognition and Tacotron for speech synthesis.
- **Secure & User-Friendly**: Designed to provide a secure, accessible, and intuitive examination experience.

## Tech Stack

- **Frontend**: HTML,CSS
- **Backend**: Python (Flask)
- **Speech Processing**: Wave2Vec 2.0, Tacotron
- **Face Recognition**: OpenCV, dlib
- **Database**: SQLite/MySQL

## Usage

- The system will prompt users with questions through audio.
- Candidates can respond verbally, and the system will transcribe their answers.
- Facial verification ensures secure access before the examination starts.
- Results and analytics can be stored and accessed for further evaluation.

## 🚀 Deployment (Render)

1. Push this project to GitHub.
2. Go to [https://render.com](https://render.com) and create a free account.
3. Click "New Web Service" and connect your GitHub repo.
4. Fill in the deployment settings:

   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3.10 or later
   - **Root Directory**: `voice_based_examination` (if app.py is inside this folder)

5. Click "Deploy" and you're live 🎉

> Make sure `auraassist.db` and other `.db` files are either included in `.gitignore` or handled securely.


## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## Contact

For any inquiries or support, contact:

- **Manem Yamani**
- Email: [manemyamani003@gmail.com]
- GitHub: [manemyamani](https://github.com/manemyamani)
## To run 
- python app.py

---
