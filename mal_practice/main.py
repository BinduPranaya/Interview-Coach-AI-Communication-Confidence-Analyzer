from utils.extract_face import extract_face_from_resume
from utils.face_verification import start_face_verification
import os

resume_path = "resume_folder/candidate_resume.pdf"
face_save_path = "resume_folder/candidate_face.jpg"

if not os.path.exists("resume_folder"):
    os.makedirs("resume_folder")

try:
    face_image_path = extract_face_from_resume(resume_path, face_save_path)
    if face_image_path and os.path.exists(face_image_path):
        start_face_verification(face_image_path)
    else:
        print("❌ No valid face image found for verification.")
except Exception as e:
    print(f"⚠️ Error: {e}")
