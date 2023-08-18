import cv2
import os
from PIL import Image, ImageSequence
import subprocess

def convert_swf_to_mp4(swf_path, output_path):
    command = f'ffmpeg -i {swf_path} -c:v libx264 -c:a aac -strict experimental -b:a 192k -ar 48000 -aspect 16:9 {output_path}'
    subprocess.call(command, shell=True)

def video_to_frames(video_path, output_dir):
    if output_dir is None or len(output_dir) == 0:
        output_dir = os.getcwd()

    # Create the directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # File extension
    extension = os.path.splitext(video_path)[1]

    if extension == '.gif':
        # Open the gif
        gif = Image.open(video_path)

        frame_number = 0
        for frame in ImageSequence.Iterator(gif):
            # Save the frame to a file
            output_file = os.path.join(output_dir, f"frame_{frame_number}.png")
            frame.save(output_file, 'PNG')

            frame_number += 1
    elif extension == '.swf':
        convert_swf_to_mp4(video_path, f"{os.path.join(output_dir, 'swf_as_vid.mp4')}")
        print(f"FLASH file converted to .mp4 file in specified folder:\t{os.path.join(video_path,output_dir)}!")
    else:
        # Load the video
        video = cv2.VideoCapture(video_path)

        # Check if video opened successfully
        if not video.isOpened():
            print("Error opening video file")

        frame_number = 0
        while video.isOpened():
            # Read the next frame
            ret, frame = video.read()

            # If frame is read correctly, ret is True
            if not ret:
                break

            # Save the frame to a file
            output_file = os.path.join(output_dir, f"frame_{frame_number}.png")
            cv2.imwrite(output_file, frame)

            frame_number += 1

        # Release the video
        video.release()
        cv2.destroyAllWindows()
