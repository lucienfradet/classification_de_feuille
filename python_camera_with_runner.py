#!/usr/bin/env python3

import cv2
import pygame
import os, sys, getopt, signal, time, random, socket
import RPi.GPIO as GPIO  # Import the GPIO library
from PIL import Image
from edge_impulse_linux.image import ImageImpulseRunner

runner = None
labels = []
# main version
# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)

# Network setup
# LAPTOP_IP = "100.69.3.55"  # Replace with your laptop's IP
# LAPTOP_PORT = 12345  # Port for debugging messages
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set up the display in fullscreen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

# Set up GPIO
BUTTON_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Button connected to GPIO 4

# Helper functions
def now():
    return round(time.time() * 1000)
def help():
    print('python python_camera_with_runner.py <path_to_model.eim>')

# def # debug_message(message):
#     """Send debug message to the laptop."""
#     try:
#         sock.sendto(message.encode(), (LAPTOP_IP, LAPTOP_PORT))
#     except Exception as e:
#         print(f"Failed to send message: {e}")

def preprocess_frame(frame):
    # Convert the frame from BGR (OpenCV default) to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Resize the frame to the model's input size
    # Replace (96, 96) with your model's expected input size
    frame_resized = cv2.resize(frame_rgb, (96, 96))
    return frame_resized

# Function to find the first available video device
videoCaptureDeviceId = 0
def find_camera_device():
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # debug_message(f"Using camera device {i}")
            global videoCaptureDeviceId
            videoCaptureDeviceId = i
            #cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
            #cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)
            return cap
        cap.release()
    # debug_message("Error: No available camera devices found.")
    exit()

# Initialize camera
cap = find_camera_device()

# Get the dimensions of the video stream (frame size)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
RESIZE_RATIO = 0.2
image_width, image_height = int(frame_width * RESIZE_RATIO), int(frame_height * RESIZE_RATIO)

# Flag to control the video feed display
button_pressed = False

# Function to display the frame centered
def display_centered_frame(frame):
    # Get the frame size
    height, width = frame.shape[:2]

    frame = cv2.resize(frame, (int(frame_width * RESIZE_RATIO), int(frame_height * RESIZE_RATIO)))

    # Rotate the frame 90 degrees counterclockwise
    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Calculate the position to center the frame
    x_offset = (screen_width - width * RESIZE_RATIO) // 2
    y_offset = (screen_height - height * RESIZE_RATIO) // 2

    # Convert the frame to Pygame format
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame_rgb)
    frame_surface = pygame.transform.rotate(frame_surface, -90)
    frame_surface = pygame.transform.flip(frame_surface, True, False)

    # Display the frame centered
    screen.fill((0, 0, 0))  # Fill the screen with black
    screen.blit(frame_surface, (x_offset, y_offset))  # Blit the frame at the calculated position
    pygame.display.flip()

# Function to capture and save an image to /tmp
def capture_image(frame):
    img_path = "/tmp/captured_image.jpg"
    cv2.imwrite(img_path, frame)
    return img_path, frame

# Function to display an image from a file path
def display_image(img_path, duration=3):
    height, width = frame.shape[:2]
    image = pygame.image.load(img_path)
    # Calculate the position to center the frame
    x_offset = (screen_width - width * RESIZE_RATIO) // 2
    y_offset = (screen_height - height * RESIZE_RATIO) // 2
    image = pygame.transform.scale(image, (image_width, image_height))
    image = pygame.transform.rotate(image, 90)
    screen.blit(image, (x_offset, y_offset))
    pygame.display.flip()
    time.sleep(duration)

# Function to display a random word
def display_result(result, score):
    # Render the random word on screen
    font_result = pygame.font.Font(None, 150)  # Large font for the result
    font_score = pygame.font.Font(None, 40)  # Smaller font for the score
    formatted_score = f"{score:.2f}"

    # Render the result
    result_surface = font_result.render(result, True, (255, 255, 255))  # White text
    result_rect = result_surface.get_rect(center=(screen_width // 2, screen_height // 2))  # Slightly higher than center

    # Render the score
    score_surface = font_score.render(formatted_score, True, (255, 255, 255))  # White text
    score_rect = score_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 90))  # Slightly below center

    # Fill the screen and blit the text
    screen.fill((0, 0, 0))  # Fill the screen with black
    screen.blit(result_surface, result_rect)  # Blit the result at the center
    screen.blit(score_surface, score_rect)  # Blit the score below the result
    pygame.display.flip()

    # Display the word for 3 seconds
    time.sleep(3)

def get_result(frame):
    # debug_message("Starting get_result function...")
    try:
        # Preprocess the frame
        preprocessed = preprocess_frame(frame)
        # Convert to PIL Image
        # img = Image.fromarray(preprocessed)
        # Get features
        features, cropped = runner.get_features_from_image(preprocessed)
        # Run classification
        res = runner.classify(features)
        # debug_message("Classification result received.")
        if "classification" in res["result"]:
            high_score = 0
            winning_label = "No match found"
            for label in labels:
                score = res['result']['classification'][label]
                if score > high_score:
                    high_score = score
                    winning_label = label
            # debug_message(f"Result: {winning_label} (Score: {high_score:.2f})")
            return winning_label, high_score
        elif "bounding_boxes" in res["result"]:
            # debug_message('Bounding box results are not supported for this setup.')
            return "Bounding box not handled"
        # debug_message("No valid result found.")
        return "No result"
    except Exception as e:
        # debug_message(f"Error during classification: {e}")
        return "Error"

# Define your callback function for button press
def button_callback(frame):
    global button_pressed
    button_pressed = True


# Set up event detection on button press
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=button_callback, bouncetime=200)

def loadModel(argv):
    global runner, labels
    try:
        opts, args = getopt.getopt(argv, "h", ["--help"])
    except getopt.GetoptError:
        help()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help()
            sys.exit()
    if len(args) == 0:
        help()
        sys.exit(2)
    model = args[0]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    modelfile = os.path.join(dir_path, model)
    # debug_message('MODEL: ' + modelfile)
    runner = ImageImpulseRunner(modelfile)
    try:
        model_info = runner.init()
        # debug_message('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
        labels = model_info['model_parameters']['labels']
    except Exception as e:
        # debug_message(f"Error loading model: {e}")
        sys.exit(1)

loadModel(sys.argv[1:])

try:
    running = True
    while running:

        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            # debug_message("Failed to grab frame.")
            break

        if not button_pressed:
            # Display the frame centered without resizing
            display_centered_frame(frame)
        else:
            # Capture and display the photo for 1 second
            result, score = get_result(preprocess_frame(frame))
            img_path, image = capture_image(frame)
            # debug_message(f"Classification result: {result}")

            display_image(img_path, duration=1)
            
            # Hide the video and display a random word for 3 seconds
            # display_random_word()
            display_result(result, score)

            button_pressed = False

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    button_pressed = True
                elif event.key == pygame.K_ESCAPE:  # Quit on 'ESC'
                    running = False

except Exception as e:
    # debug_message(f"An error occurred: {e}")
    print(e)
finally:
    # Release resources
    cap.release()
    pygame.quit()
    if (runner):
        runner.stop()
    GPIO.cleanup()  # Clean up GPIO settings
