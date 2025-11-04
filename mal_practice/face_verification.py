import cv2
import face_recognition
import numpy as np
import winsound

def start_face_verification(known_face_path):
    known_img = face_recognition.load_image_file(known_face_path)
    known_encoding = face_recognition.face_encodings(known_img)[0]

    video = cv2.VideoCapture(0)
    print("Press 'q' to quit the interview monitoring...")

    while True:
        ret, frame = video.read()
        if not ret:
            print("⚠️ Camera not accessible.")
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces([known_encoding], face_encoding)
            face_distances = face_recognition.face_distance([known_encoding], face_encoding)
            name = "Intruder"

            if matches[0] and face_distances[0] < 0.5:
                name = "Candidate"

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            if name == "Candidate":
                color = (0, 255, 0)  # Green
            else:
                color = (0, 0, 255)  # Red
                winsound.Beep(1000, 500)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow("AI Interview Face Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()
    print("🔺 Monitoring stopped manually.")
