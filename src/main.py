from collections.abc import Sequence

import argparse
import cv2
from cv2.typing import MatLike
import mediapipe as mp
from mediapipe.tasks.python.vision.hand_landmarker import (
  HandLandmarker,
  HandLandmarkerResult,
)
import time
import os
from pathlib import Path
from gestures.config import load_config

def create_landmarker() -> HandLandmarker:
  options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
      model_asset_path="models/hand_landmarker.task"
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1,
  )

  landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
  return landmarker

HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
  (0, 1), (1, 2), (2, 3), (3, 4),                   # Thumb      
  (0, 5), (5, 6), (6, 7), (7, 8),                   # Index       
  (5, 9), (9, 10), (10, 11), (11, 12),              # Middle       
  (9, 13), (13, 14), (14, 15), (15, 16),            # Ring       
  (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky   
)
def draw_hands(
  frame: MatLike,
  result: HandLandmarkerResult,
) -> None:
  height, width = frame.shape[:2]

  for hand in result.hand_landmarks:
    points = [
      (int(point.x * width), int(point.y * height))
      for point in hand
    ]

    for start, end in HAND_CONNECTIONS:
      cv2.line(
        frame, points[start], points[end],
        (0, 255, 0), 2,
      )

    for point in points:
      cv2.circle(frame, point, 4, (0, 0, 255), -1)

def show_webcam() -> None:
  camera = cv2.VideoCapture(0)
  if not camera.isOpened():
    raise RuntimeError("Hardware: Could not open webcam")

  try:
    landmarker = create_landmarker()
  except:
    raise RuntimeError("Landmarker: Could not create a landmarker")
  
  try:
    last_timestamp_ms = -1
    
    while True:
      success, frame = camera.read()
      if not success:
        raise RuntimeError("VideoCapture: Could not read webcam frame")
      
      rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

      timestamp_ms = max(
        time.monotonic_ns() // 1_000_000,
        last_timestamp_ms + 1,
      )

      result = landmarker.detect_for_video(image, timestamp_ms)
      draw_hands(frame, result)

      # Mirror after drawing so the skeleton stays aligned
      cv2.imshow("Webcam", cv2.flip(frame, 1))

      if cv2.waitKey(1) & 0xFF == ord("q"):
        break
  finally:
    camera.release()
    cv2.destroyAllWindows()
    landmarker.close()
 
def main(argv: Sequence[str] | None = None) -> None:
  parser = argparse.ArgumentParser(description="Coordinator of your workspaces")
  parser.add_argument("--live-visual", action="store_true")
  args = parser.parse_args(argv)

  config_home = os.environ.get("XDG_CONFIG_HOME")
  if config_home and Path(config_home).is_absolute:
    config_root = Path(config_home)
  else:
    config_root = Path.home() / ".config"
  cordie_file = config_root / "cordie" / "cordie.toml"
  config = load_config(cordie_file)

  if args.live_visual:
    show_webcam()

if __name__ == "__main__":
  main()

