from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO, emit

import cv2
import mediapipe as mp
import math

app = Flask(__name__)
socketio = SocketIO(app)

camera = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


def calculate_distance(point1, point2):
    return math.sqrt(
        (point2.x - point1.x)  2 +
        (point2.y - point1.y)  2 +
        (point2.z - point1.z) ** 2
    )


def calculate_angle(p1, p2):
    delta_y = p2[1] - p1[1]
    delta_x = p2[0] - p1[0]
    angle = math.degrees(math.atan2(delta_y, delta_x))
    return angle


def calculate_horizontal_offset(wrist, frame_width):
    center_x = frame_width / 2
    offset = (wrist.x * frame_width) - center_x
    return offset


def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                distance = calculate_distance(thumb_tip, index_tip)

                z_distance = index_tip.z - wrist.z
                x_distance = index_tip.x - wrist.x

                wrist_coords = (int(wrist.x * frame.shape[1]), int(wrist.y * frame.shape[0]))
                index_finger_coords = (int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0]))

                angle = calculate_angle(wrist_coords, index_finger_coords)

                horizontal_offset = calculate_horizontal_offset(wrist, frame.shape[1])

                cv2.putText(frame, f'C90 (M): {round(distance, 2)}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, f'M180 (F): {int(angle)} degrees', (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, f'B360 (Z): {round(z_distance, 2)}', (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f'R90 (Y): {round(x_distance, 2)}', (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/student', methods=["GET"])
def student_GET():
    return jsonify([
        'Student 1',
        'Student 2',
        'Student 3',
        'Student 4',
        'Student 5',
    ])


@app.route('/student', methods=["POST"])
def student_POST():
    data = request.get_json()
    print(data)
    return jsonify([
        'Student registered'
    ])


@app.route('/student', methods=["PUT"])
def student_PUT():
    data = request.get_json()
    print(data)
    return jsonify([
        'Student updateed'
    ])


@app.route('/student', methods=["DELETE"])
def student_DELETE():
    data = request.get_json()
    print(data)
    return jsonify([
        'Student deleted'
    ])


@socketio.on('info')
def info(msg):
    print('Received message: ' + msg)
    emit('response', {'data': 'Message received!'})


@socketio.on('connect')
def handle_connect():
    print('Client connected')