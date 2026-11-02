import imageio.v3 as iio
import numpy as np

frames = [
    iio.imread("assets/gameplay_frame_01.jpg"),
    iio.imread("assets/gameplay_frame_02.jpg"),
    iio.imread("assets/gameplay_frame_03.jpg"),
]

# Повторяем каждый кадр несколько раз для плавности (2 сек на кадр = 30 кадров при 15 fps)
video_frames = []
for f in frames:
    for _ in range(30):
        video_frames.append(f)

# Сохраняем в MP4 (imageio-ffmpeg использует ffmpeg под капотом)
iio.imwrite("build_gameplay.mp4", video_frames, fps=15, quality=8, codec="libx264")
print("Видео собрано: build_gameplay.mp4 (3 кадра билда, 15 fps, ~6 сек)")
print("Это визуальная документация текущего среза (Godot 4.3, Forward+, мобильный HUD, AI Griever).")
print("Для реального геймплея — запусти проект на Poco F4 или ПК с Godot 4.3 и снимай экран.")
