# modules/asset_loader.py — 加载所有素材

import os
import numpy as np
from PIL import Image
from moviepy import VideoFileClip, AudioFileClip, ImageClip


def load_icons(icons_dir, target_icon_path, min_count=5):
    """加载图标文件夹中所有图片，不足 min_count 个时循环复制"""
    supported = ('.png', '.jpg', '.jpeg', '.webp')
    icon_files = []

    if os.path.isdir(icons_dir):
        for f in sorted(os.listdir(icons_dir)):
            if f.lower().endswith(supported):
                icon_files.append(os.path.join(icons_dir, f))

    # 确保目标图标在列表中
    if target_icon_path and os.path.exists(target_icon_path):
        target_icon_path = os.path.abspath(target_icon_path)
        if target_icon_path not in [os.path.abspath(p) for p in icon_files]:
            icon_files.append(target_icon_path)

    if not icon_files:
        return [], None

    # 少于 min_count 个时循环复制
    original_count = len(icon_files)
    target_idx = -1
    for i, f in enumerate(icon_files):
        if os.path.abspath(f) == os.path.abspath(target_icon_path):
            target_idx = i
            break

    if original_count < min_count:
        repeats = (min_count // original_count) + 1
        icon_files = icon_files * repeats
        if target_idx >= 0:
            target_idx = target_idx  # 保持第一个目标图标位置不变

    return icon_files, target_idx


def load_background(bg_path, width, height, duration, fps):
    """加载背景素材（支持视频和图片），有错误时降级为渐变"""
    if not bg_path or not os.path.exists(bg_path):
        return _create_gradient_bg(width, height, duration)

    try:
        ext = os.path.splitext(bg_path)[1].lower()
        if ext in ('.mp4', '.mov', '.avi', '.webm', '.mkv'):
            clip = VideoFileClip(bg_path, audio=False).resized((width, height))
            return clip.subclipped(0, min(duration, clip.duration))
        else:
            return ImageClip(bg_path).resized((width, height)).with_duration(duration)
    except Exception as e:
        print(f"  警告: 背景加载失败 ({e})，使用默认渐变")
        return _create_gradient_bg(width, height, duration)


def _create_gradient_bg(width, height, duration):
    """生成暗色渐变背景"""
    import numpy as np
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        t = y / height
        gradient[y, :] = [int(10 + 30 * t), int(10 + 20 * t), int(30 + 50 * t)]
    return ImageClip(gradient).with_duration(duration)


def load_audio(bgm_path, sfx_paths, duration):
    """加载背景音乐和音效，返回 (bgm_clip, sfx_dict)"""
    bgm = None
    if bgm_path and os.path.exists(bgm_path):
        try:
            bgm = AudioFileClip(bgm_path)
            if bgm.duration < duration:
                bgm = bgm.with_effects([bgm.loop(duration=duration)])
            else:
                bgm = bgm.subclipped(0, duration)
            bgm = bgm.with_volume(0.3)
        except Exception:
            bgm = None

    sfx = {}
    for name, path in sfx_paths.items():
        if path and os.path.exists(path):
            try:
                sfx[name] = AudioFileClip(path)
            except Exception:
                sfx[name] = None
        else:
            sfx[name] = None

    return bgm, sfx


def load_intro_clip(clip_path, width, height):
    """加载实录视频，取前 1.5 秒"""
    if not clip_path or not os.path.exists(clip_path):
        return None

    try:
        clip = VideoFileClip(clip_path).resized((width, height))
        duration = min(1.5, clip.duration)
        return clip.subclipped(0, duration)
    except Exception:
        return None


def load_icon_images(icon_files, icon_size):
    """将图标文件加载为统一大小的 numpy 数组"""
    images = []
    for path in icon_files:
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize((icon_size, icon_size), Image.LANCZOS)
            images.append(np.array(img))
        except Exception:
            continue
    return images
