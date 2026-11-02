#!/bin/bash
# Сборка видео геймплея из кадров (используй на любом ПК с ffmpeg)
# Кадры из текущего билда: gameplay_frame_01/02/03.jpg
# Для реального геймплея — запусти Godot 4.3 и используй ffmpeg -f x11grab / screen capture.

ffmpeg -framerate 6 -i assets/gameplay_frame_%02d.jpg -c:v libx264 -pix_fmt yuv420p -r 30 -y build_gameplay.mp4

echo "Видео готово: build_gameplay.mp4 (6 fps, 3 кадра среза)"
echo "Для настоящего геймплея замени кадры на запись экрана из Godot:"
echo "ffmpeg -f x11grab -r 30 -i :0.0 -c:v libx264 -preset ultrafast gameplay_real.mp4"
