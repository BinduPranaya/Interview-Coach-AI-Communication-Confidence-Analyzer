# emotion_model.py

import cv2
import numpy as np
# from tensorflow.keras.models import load_model # Uncomment when the model file is available
import os

# Suppress the oneDNN warning
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Constants
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
MODEL_PATH = 'emotion_model.h5'
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

class EmotionPredictor:
    """
    Stateless class to handle image preprocessing and emotion prediction.
    It is initialized once by FastAPI and reused across requests.
    """
    def __init__(self):
        print("Initializing EmotionPredictor...")
        
        # Load the Haar Cascade once
        self.face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
        if self.face_cascade.empty():
            print(f"Error: Could not load Haar cascade from {CASCADE_PATH}")
            # Consider raising an exception or having a fallback
        
        # --- Model Loading (Uncomment when available) ---
        # try:
        #     self.model = load_model(MODEL_PATH)
        #     print(f"Successfully loaded model from {MODEL_PATH}")
        # except Exception as e:
        #     self.model = None
        #     print(f"Warning: Could not load Keras model: {e}")
        
        # Dummy model placeholder for initial testing
        self.model = None
        print("Using DUMMY predictions. Load 'emotion_model.h5' for real predictions.")


    def preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """Preprocess a face image for the model input (48x48, grayscale, normalized)."""
        face_img = cv2.resize(face_img, (48, 48))
        # Ensure image is in grayscale (needed for the FER-2013 model architecture)
        if len(face_img.shape) == 3 and face_img.shape[2] == 3:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
        face_img = face_img / 255.0
        # Model expects a batch of 48x48x1 images: (1, 48, 48, 1)
        return np.expand_dims(np.expand_dims(face_img, -1), 0)

    
    def predict_emotion(self, image_data: bytes) -> dict:
        """
        Detects faces and predicts emotion from raw image bytes.
        Returns a dictionary containing prediction results.
        """
        # Convert raw bytes to a NumPy array (image)
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"status": "error", "message": "Could not decode image."}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(faces) == 0:
            return {"status": "no_face_detected", "emotion": "N/A", "confidence": 0.0, "rect": None}

        # Focus on the largest/first face
        (x, y, w, h) = faces[0]
        face_roi = frame[y:y+h, x:x+w]
        processed_face = self.preprocess_face(face_roi)

        emotion = "N/A"
        confidence = 0.0

        if self.model:
            # ACTUAL MODEL PREDICTION
            prediction = self.model.predict(processed_face, verbose=0)
            emotion = EMOTION_LABELS[np.argmax(prediction)]
            confidence = float(np.max(prediction))
        else:
            # DUMMY PREDICTION (Replace this block with the 'if self.model:' block)
            emotion = np.random.choice(EMOTION_LABELS)
            confidence = float(np.random.random())
        
        return {
            "status": "success",
            "emotion": emotion,
            "confidence": round(confidence, 4),
            "rect": (int(x), int(y), int(w), int(h)) # Bounding box for client display
        }