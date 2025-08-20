import cv2
import mediapipe as mp

# Initialize MediaPipe and OpenCV
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1)

cap = cv2.VideoCapture(0)

# Tip landmarks
tip_ids = [4, 8, 12, 16, 20]

# States
STATE_INPUT_FIRST = 0
STATE_WAIT_OPERATOR = 1
STATE_INPUT_OPERATOR = 2
STATE_WAIT_SECOND = 3
STATE_INPUT_SECOND = 4
STATE_SHOW_RESULT = 5

state = STATE_INPUT_FIRST

first_num = None
second_num = None
operation = None
result = None

cooldown_counter = 0
cooldown = 20

op_map = {
    1: '+',
    2: '-',
    3: '*',
    4: '/',
}


def count_fingers(hand_landmarks):
    fingers = []

    # Thumb
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Other fingers
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[tip_ids[id] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return sum(fingers)


while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    finger_count = -1

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand_landmarks)

    if cooldown_counter > 0:
        cooldown_counter -= 1
        finger_count = -1  # Ignore finger count during cooldown

    if finger_count != -1:
        # FSM - Finite State Machine
        if state == STATE_INPUT_FIRST and finger_count > 0:
            first_num = finger_count
            state = STATE_WAIT_OPERATOR
            cooldown_counter = cooldown

        elif state == STATE_WAIT_OPERATOR and finger_count == 0:
            state = STATE_INPUT_OPERATOR
            cooldown_counter = cooldown

        elif state == STATE_INPUT_OPERATOR and finger_count in op_map:
            operation = op_map[finger_count]
            state = STATE_WAIT_SECOND
            cooldown_counter = cooldown

        elif state == STATE_WAIT_SECOND and finger_count == 0:
            state = STATE_INPUT_SECOND
            cooldown_counter = cooldown

        elif state == STATE_INPUT_SECOND and finger_count > 0:
            second_num = finger_count
            state = STATE_SHOW_RESULT
            cooldown_counter = cooldown

        elif state == STATE_SHOW_RESULT:
            # Should not reach here again unless reset
            pass

    # Calculation
    if state == STATE_SHOW_RESULT:
        if operation == '+':
            result = first_num + second_num
        elif operation == '-':
            result = first_num - second_num
        elif operation == '*':
            result = first_num * second_num
        elif operation == '/':
            result = round(first_num / second_num, 2) if second_num != 0 else "∞"

    # Display
    display_text = ""

    if first_num is not None:
        display_text += str(first_num)

    if operation is not None:
        display_text += f" {operation} "

    if second_num is not None:
        display_text += str(second_num)

    if result is not None:
        display_text += f" = {result}"

    if state == STATE_INPUT_FIRST:
        info = "Show first number"
    elif state == STATE_WAIT_OPERATOR:
        info = "Closed fist to confirm"
    elif state == STATE_INPUT_OPERATOR:
        info = "1:+ 2:- 3:* 4:/"
    elif state == STATE_WAIT_SECOND:
        info = "Closed fist to continue"
    elif state == STATE_INPUT_SECOND:
        info = "Show second number"
    elif state == STATE_SHOW_RESULT:
        info = "Result shown. Press 'r' to reset."

    # Show display text
    cv2.putText(frame, display_text, (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (101, 18, 230), 4)
    cv2.putText(frame, info, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (217,1,122), 2)

    cv2.imshow("Gesture Calculator", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('r'):
        # Reset everything
        state = STATE_INPUT_FIRST
        first_num = second_num = operation = result = None
        cooldown_counter = cooldown

cap.release()
cv2.destroyAllWindows()


