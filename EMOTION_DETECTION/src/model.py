import cv2
from deepface import DeepFace

# Initialize webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Analyze emotions using DeepFace
    try:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)

        # Extract dominant emotion
        emotion = results[0]['dominant_emotion']

        # Display emotion text on frame
        cv2.putText(frame, f"Emotion: {emotion}", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    except Exception as e:
        print("Error analyzing frame:", e)

    # Show the video frame
    cv2.imshow("AI Emotion Detection (DeepFace)", frame)

    # Press ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
