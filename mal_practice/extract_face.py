import fitz  # PyMuPDF
import cv2
import numpy as np
import os

def extract_face_from_resume(pdf_path, save_path):
    """Extracts the first face found in a resume PDF and saves it."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"❌ Resume not found at: {pdf_path}")

    print("📄 Extracting candidate photo from resume...")

    # Open the PDF
    doc = fitz.open(pdf_path)
    for page_index in range(len(doc)):
        images = doc.get_page_images(page_index)
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]

            # Convert to OpenCV format
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)

            # Detect face
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                (x, y, w, h) = faces[0]
                face = image[y:y+h, x:x+w]
                cv2.imwrite(save_path, face)
                print(f"✅ Candidate face extracted successfully: {save_path}")
                doc.close()
                return save_path

    doc.close()
    print("⚠️ No face detected in resume.")
    return None
