import face_recognition
import cv2
import numpy as np
import time
import webbrowser
import os
import pyttsx3
import PyPDF2
import re
from typing import Dict
import threading
import subprocess

class InstructionSystem:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)

    def pdf_to_text(self) -> str:
        """Extract text from PDF file"""
        with open(self.pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            pdf_text = ''
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_text += page.extract_text()
        return pdf_text

    def clean_text_for_speech(self, text: str) -> str:
        """Clean and normalize text for speech"""
        text = ' '.join(text.split())
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*([.,!?:;])\s*', r'\1 ', text)
        return text.strip()

    def read_instructions(self):
        """Read instructions aloud"""
        text = self.pdf_to_text()
        cleaned_text = self.clean_text_for_speech(text)
        sentences = re.split('([.!?])', cleaned_text)
        
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
                if sentence.strip():
                    self.engine.say(sentence)
                    self.engine.runAndWait()

    def open_pdf(self):
        """Open PDF file using default system viewer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.pdf_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['xdg-open', self.pdf_path])
        except Exception as e:
            print(f"Error opening PDF: {str(e)}")

    def start_instruction_session(self):
        """Start both PDF display and audio instructions"""
        # Open PDF in a separate thread
        pdf_thread = threading.Thread(target=self.open_pdf)
        pdf_thread.start()
        
        # Start reading instructions in a separate thread
        speech_thread = threading.Thread(target=self.read_instructions)
        speech_thread.start()

class MultiUserFaceVerification:
    def __init__(self, reference_images_dir: str, instruction_system: InstructionSystem):
        self.known_face_encodings = []
        self.known_user_ids = []
        self.instruction_system = instruction_system
        self.load_reference_images(reference_images_dir)
        
    def load_reference_images(self, directory: str) -> None:
        """Load and encode all reference images from the directory"""
        print("Loading reference images...")
        for filename in os.listdir(directory):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                user_id = filename.split('.')[0]
                image_path = os.path.join(directory, filename)
                
                try:
                    known_image = face_recognition.load_image_file(image_path)
                    face_locations = face_recognition.face_locations(known_image, model="hog")
                    
                    if face_locations:
                        face_encoding = face_recognition.face_encodings(known_image, face_locations)[0]
                        self.known_face_encodings.append(face_encoding)
                        self.known_user_ids.append(user_id)
                        print(f"Loaded reference image for user: {user_id}")
                    else:
                        print(f"No face found in reference image for user: {user_id}")
                except Exception as e:
                    print(f"Error loading reference image for user {user_id}: {str(e)}")

    def verify_single_user(self, duration: int = 25, required_matches: int = 5) -> Dict[str, bool]:
        verified_users = {}
        consecutive_matches = {user_id: 0 for user_id in self.known_user_ids}
        
        try:
            video_capture = cv2.VideoCapture(0)
            if not video_capture.isOpened():
                raise Exception("Could not access webcam")

            start_time = time.time()
            frame_count = 0
            
            while True:
                elapsed_time = time.time() - start_time
                if elapsed_time > duration:
                    print("Time expired!")
                    break
                
                ret, frame = video_capture.read()
                if not ret:
                    continue

                # Process every 2nd frame for better performance
                frame_count += 1
                if frame_count % 2 != 0:
                    self._display_status(frame, elapsed_time, duration)
                    cv2.imshow('Exam Login', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue

                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Find and process faces in current frame
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    # Check each detected face against all known faces
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(
                            self.known_face_encodings, 
                            face_encoding,
                            tolerance=0.5
                        )
                        
                        if True in matches:
                            face_distances = face_recognition.face_distance(
                                self.known_face_encodings,
                                face_encoding
                            )
                            best_match_index = np.argmin(face_distances)
                            
                            if face_distances[best_match_index] < 0.4:  # Strict threshold
                                user_id = self.known_user_ids[best_match_index]
                                consecutive_matches[user_id] += 1
                                
                                if consecutive_matches[user_id] >= required_matches:
                                    verified_users[user_id] = True
                                    
                                    # Display success message
                                    cv2.putText(frame, "Verification Successful!", (10, frame.shape[0] - 30),
                                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                    cv2.imshow('Exam Login', frame)
                                    cv2.waitKey(1000)  # Show success message for 1 second
                                    
                                    # Cleanup
                                    video_capture.release()
                                    cv2.destroyAllWindows()
                                    
                                    print(f"User {user_id} verified successfully!")
                                    print("Starting instruction session...")
                                    self.instruction_system.start_instruction_session()
                                    return verified_users
                                
                                # Draw rectangle around matched face
                                top, right, bottom, left = [coord * 4 for coord in face_locations[0]]
                                color = (0, 255, 255)  # Yellow for pending verification
                                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                                cv2.putText(frame, f"Verifying: {user_id}", (left, top - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
                            else:
                                # Reset consecutive matches if face distance is too high
                                consecutive_matches[user_id] = 0
                        else:
                            # Draw red rectangle around unrecognized face
                            top, right, bottom, left = [coord * 4 for coord in face_locations[0]]
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                            cv2.putText(frame, "Invalid Face", (left, top - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                
                self._display_status(frame, elapsed_time, duration)
                cv2.imshow('Exam Login', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Cleanup if verification fails
            video_capture.release()
            cv2.destroyAllWindows()
            print("Verification failed - time expired")
            return verified_users
            
        except Exception as e:
            print(f"Error during face verification: {str(e)}")
            if 'video_capture' in locals():
                video_capture.release()
            cv2.destroyAllWindows()
            return verified_users

    def _display_status(self, frame: np.ndarray, elapsed_time: float, duration: int) -> None:
        """Display status information on the frame"""
        remaining_time = max(0, duration - elapsed_time)
        cv2.putText(frame, f"Time remaining: {remaining_time:.1f}s", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.75, 
                   (0, 255, 0) if remaining_time > 5 else (0, 0, 255), 2)

def main():
    # Paths configuration
    reference_dir = r".\reference_images"
    instructions_pdf = r".\instructions.pdf"
    
    # Initialize instruction system
    instruction_system = InstructionSystem(instructions_pdf)
    
    # Initialize face verification with instruction system
    verifier = MultiUserFaceVerification(reference_dir, instruction_system)
    
    # Start verification with 25-second timeout
    verified_users = verifier.verify_single_user(duration=50)
    
    # Print final results
    if verified_users:
        print("\nVerification and instruction session completed!")
        for user_id in verified_users:
            print(f"Verified user: {user_id}")
    else:
        print("\nVerification failed - no users verified within time limit")

if __name__ == "__main__":
    main()