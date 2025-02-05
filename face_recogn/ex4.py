import face_recognition
import cv2
import numpy as np
import time
import webbrowser
import os
from typing import Dict, List, Tuple
import pyttsx3
from bs4 import BeautifulSoup
import threading
import re
import sys

class ExamPlatform:
    def __init__(self, reference_images_dir: str, instructions_html: str):
        """
        Initialize the exam platform
        
        Args:
            reference_images_dir (str): Directory containing reference images
            instructions_html (str): Path to the HTML instructions file
        """
        self.face_verifier = MultiUserFaceVerification(reference_images_dir)
        self.instructions_html = instructions_html
        self.tts_engine = None  # Initialize later
        self.instruction_complete = threading.Event()
        
    def setup_tts(self):
        """Configure text-to-speech settings"""
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
    
    def start_exam_session(self):
        """Start the exam session with verification and instructions"""
        try:
            # Step 1: Verify user
            verified_users = self.face_verifier.verify_single_user(duration=25)
            
            if verified_users:
                print("\nUser verified successfully! Opening instructions...")
                # Step 2: Open HTML and read instructions
                self.present_instructions()
                
                # Wait for instructions to complete
                print("Waiting for instructions to complete...")
                self.instruction_complete.wait()
                print("Instructions completed. You may now proceed with the exam.")
                
                # Add a small delay before exit
                time.sleep(2)
            else:
                print("\nVerification failed. Please try again.")
                
        except Exception as e:
            print(f"Error in exam session: {str(e)}")
        finally:
            # Cleanup
            if self.tts_engine:
                self.tts_engine.stop()
            
    def extract_instructions_from_html(self) -> str:
        """Extract instruction text from HTML file"""
        try:
            with open(self.instructions_html, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                instruction_items = soup.find_all('div', {'class': 'instruction-item'})
                
                if instruction_items:
                    return ' '.join(item.get_text(strip=True) for item in instruction_items)
                else:
                    # Fallback to body text
                    body_text = soup.find('body')
                    if body_text:
                        return body_text.get_text(strip=True)
                    else:
                        raise Exception("No instruction text found in HTML")
                    
        except Exception as e:
            print(f"Error extracting instructions from HTML: {str(e)}")
            return None
            
    def present_instructions(self):
        """Present and read out exam instructions"""
        try:
            # Open HTML file in browser
            full_path = os.path.abspath(self.instructions_html)
            print(f"Opening instructions at: {full_path}")
            webbrowser.open('file://' + full_path)
            
            # Initialize TTS engine in the main thread
            self.setup_tts()
            
            # Extract instructions
            instructions_text = self.extract_instructions_from_html()
            if instructions_text:
                # Start reading instructions in a separate thread
                instruction_thread = threading.Thread(
                    target=self.read_instructions,
                    args=(instructions_text,),
                    daemon=False  # Change to non-daemon thread
                )
                instruction_thread.start()
            else:
                print("Failed to extract instructions text.")
                self.instruction_complete.set()
                        
        except Exception as e:
            print(f"Error presenting instructions: {str(e)}")
            self.instruction_complete.set()
    
    def read_instructions(self, text: str):
        """Read the instructions text"""
        try:
            cleaned_text = self.clean_text_for_speech(text)
            print("\nReading instructions... Please listen carefully.")
            print(f"Full text to be read: {cleaned_text}")  # Debug print
            
            # Split text into complete sentences
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
            
            for sentence in sentences:
                if sentence.strip():
                    print(f"Reading sentence: {sentence}")  # Debug print
                    self.tts_engine.say(sentence)
                    self.tts_engine.runAndWait()
            
            print("\nInstructions reading completed.")
            
        except Exception as e:
            print(f"Error reading instructions: {str(e)}")
        finally:
            self.instruction_complete.set()
    
    def clean_text_for_speech(self, text: str) -> str:
        """Clean and normalize text for speech"""
        text = ' '.join(text.split())
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*([.,!?:;])\s*', r'\1 ', text)
        return text.strip()

class MultiUserFaceVerification:
    def __init__(self, reference_images_dir: str):
        self.known_face_encodings = []
        self.known_user_ids = []
        self.load_reference_images(reference_images_dir)
        
    def load_reference_images(self, directory: str) -> None:
        """Load and encode reference images"""
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

    def verify_single_user(self, duration: int = 25) -> Dict[str, bool]:
        """Verify single user with webcam"""
        verified_users = {}
        consecutive_matches = {user_id: 0 for user_id in self.known_user_ids}
        required_matches = 5
        
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

                frame_count += 1
                if frame_count % 2 != 0:
                    self._display_status(frame, elapsed_time, duration)
                    cv2.imshow('Exam Login', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    continue

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
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
                            
                            if face_distances[best_match_index] < 0.4:
                                user_id = self.known_user_ids[best_match_index]
                                consecutive_matches[user_id] += 1
                                
                                if consecutive_matches[user_id] >= required_matches:
                                    verified_users[user_id] = True
                                    cv2.putText(frame, "Verification Successful!", 
                                              (10, frame.shape[0] - 30),
                                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                    cv2.imshow('Exam Login', frame)
                                    cv2.waitKey(1000)
                                    video_capture.release()
                                    cv2.destroyAllWindows()
                                    return verified_users
                                
                                top, right, bottom, left = [coord * 4 for coord in face_locations[0]]
                                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 255), 2)
                                cv2.putText(frame, f"Verifying: {user_id}", (left, top - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)
                            else:
                                consecutive_matches[user_id] = 0
                        else:
                            top, right, bottom, left = [coord * 4 for coord in face_locations[0]]
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                            cv2.putText(frame, "Invalid Face", (left, top - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                
                self._display_status(frame, elapsed_time, duration)
                cv2.imshow('Exam Login', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            video_capture.release()
            cv2.destroyAllWindows()
            return verified_users
            
        except Exception as e:
            print(f"Error during face verification: {str(e)}")
            if 'video_capture' in locals():
                video_capture.release()
            cv2.destroyAllWindows()
            return verified_users

    def _display_status(self, frame: np.ndarray, elapsed_time: float, duration: int) -> None:
        """Display status information on frame"""
        remaining_time = max(0, duration - elapsed_time)
        cv2.putText(frame, f"Time remaining: {remaining_time:.1f}s", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.75, 
                   (0, 255, 0) if remaining_time > 5 else (0, 0, 255), 2)


def main():
    try:
        # Configuration
        reference_dir = r"./reference_images"
        instructions_html = r"../templates/instructions.html"
        
        # Initialize and start exam platform
        platform = ExamPlatform(reference_dir, instructions_html)
        platform.start_exam_session()
        
    except KeyboardInterrupt:
        print("\nExam platform shutting down...")
    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()