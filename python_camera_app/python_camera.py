import cv2
import pygame
import time
import os
import random

# Initialize Pygame
pygame.init()

# Set up the display in fullscreen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()

# Function to find the first available video device
def find_camera_device():
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Using camera device {i}")
            return cap
        cap.release()
    print("Error: No available camera devices found.")
    exit()

# Initialize camera
cap = find_camera_device()

# Get the dimensions of the video stream (frame size)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
RESIZE_RATIO = 1.8
image_width, image_height = int(frame_width * RESIZE_RATIO), int(frame_height * RESIZE_RATIO)

# Function to display the frame centered
def display_centered_frame(frame):
    # Get the frame size
    height, width = frame.shape[:2]
    
    frame = cv2.resize(frame, (int(frame_width * RESIZE_RATIO), int(frame_height * RESIZE_RATIO)))

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
    return img_path

# Function to display an image from a file path
def display_image(img_path, duration=3):
    height, width = frame.shape[:2]
    image = pygame.image.load(img_path)
    # Calculate the position to center the frame
    x_offset = (screen_width - width * RESIZE_RATIO) // 2
    y_offset = (screen_height - height * RESIZE_RATIO) // 2
    image = pygame.transform.scale(image, (image_width, image_height))
    screen.blit(image, (x_offset, y_offset))
    pygame.display.flip()
    time.sleep(duration)

# Function to display a random word
def display_random_word():
    words = ["Érable", "Frêne", "Chêne", "Banji"]
    random_word = random.choice(words)

    # Render the random word on screen
    font = pygame.font.Font(None, 800)  # You can adjust the size here
    text_surface = font.render(random_word, True, (255, 255, 255))  # White text
    text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))

    screen.fill((0, 0, 0))  # Fill the screen with black
    screen.blit(text_surface, text_rect)  # Blit the text at the center
    pygame.display.flip()

    # Display the word for 3 seconds
    time.sleep(3)

try:
    running = True
    while running:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Display the frame centered without resizing
        display_centered_frame(frame)

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Capture and display the photo for 1 second
                    img_path = capture_image(frame)
                    display_image(img_path, duration=1)
                    
                    # Hide the video and display a random word for 3 seconds
                    display_random_word()

                    # After displaying the word, return to the video feed
                    display_centered_frame(frame)

                elif event.key == pygame.K_ESCAPE:  # Quit on 'ESC'
                    running = False

finally:
    # Release resources
    cap.release()
    pygame.quit()
