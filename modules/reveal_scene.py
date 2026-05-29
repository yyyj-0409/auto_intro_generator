# modules/reveal_scene.py — v2.2 清晰揭晓: 480px, 轻雾, 微shake

import numpy as np
from PIL import Image
from moviepy import VideoClip
from modules.effects import (
    flash_frame, rgb_shift, rounded_icon, dark_bg_gradient,
    cubic_bezier_bounce, add_film_grain, color_grade,
    create_particle_burst, render_particle_burst,
    create_shockwave_ring, render_shockwave,
    create_light_rays, render_light_rays,
    draw_vignette, apply_post_processing,
)


def create_reveal_scene(target_image, config, duration):
    width = config["project"]["width"]
    height = config["project"]["height"]
    fps = config["project"]["fps"]
    target_size = 480

    if target_image is None:
        target_image = np.ones((target_size, target_size, 4), dtype=np.uint8) * [60, 60, 100, 255]

    polished = rounded_icon(target_image, 24, shadow=False)
    target_arr = np.array(Image.fromarray(polished))

    bg = dark_bg_gradient(width, height)
    n_frames = int(duration * fps)
    frames = []
    cx, cy = width // 2, height // 2 - 40

    # 预计算粒子/光芒效果数据
    eff_cfg = config.get("effects", {})
    if eff_cfg.get("particle_burst", {}).get("enabled", True):
        burst = create_particle_burst(
            cx, cy,
            num=eff_cfg["particle_burst"].get("count", 30),
            max_radius=eff_cfg["particle_burst"].get("max_radius", 500),
            duration=eff_cfg["particle_burst"].get("duration", 0.5))
    else:
        burst = None

    if eff_cfg.get("shockwave", {}).get("enabled", True):
        shockwave = create_shockwave_ring(
            cx, cy,
            max_radius=eff_cfg["shockwave"].get("max_radius", 650),
            duration=eff_cfg["shockwave"].get("duration", 0.4))
    else:
        shockwave = None

    if eff_cfg.get("light_rays", {}).get("enabled", True):
        rays = create_light_rays(
            cx, cy,
            num_rays=eff_cfg["light_rays"].get("count", 12),
            max_length=eff_cfg["light_rays"].get("max_length", 600),
            duration=eff_cfg["light_rays"].get("duration", 0.45))
    else:
        rays = None

    for fi in range(n_frames):
        t = fi / fps
        frame = bg.copy()

        # 弹性缩放 (cubic-bezier bounce)
        p = min(1.0, t / 0.25)
        bounce = 0.5 + 0.5 * cubic_bezier_bounce(p)
        sz = max(10, int(target_size * bounce))
        scaled = np.array(Image.fromarray(target_arr).resize((sz, sz), Image.LANCZOS))
        sx, sy = cx - sz // 2, cy - sz // 2
        _paste(frame, scaled, sx, sy)

        # 轻 shake
        if t < 0.15:
            shake = int(3 * (1 - t / 0.15))
            dx = int(np.sin(t * 40) * shake)
            dy = int(np.cos(t * 50) * shake)
            frame = np.roll(frame, (dy, dx), axis=(0, 1))

        # 轻闪白
        if t > 0.05 and t < 0.25:
            frame = flash_frame(frame, t, 0.05, 0.12, 140, radial=False)

        # 轻色差
        if t > 0.03 and t < 0.2:
            frame = rgb_shift(frame, t, 0.03, 0.15, 3)

        # 粒子爆发 + 冲击波 + 光芒放射
        if burst is not None:
            render_particle_burst(frame, t, burst)
        if shockwave is not None:
            render_shockwave(frame, t, shockwave)
        if rays is not None:
            render_light_rays(frame, t, rays)

        # 全局后处理
        frame = apply_post_processing(frame, config)
        frames.append(frame)

    def make_frame(t):
        return frames[min(int(t * fps), n_frames - 1)]

    return VideoClip(make_frame, duration=duration)


def _paste(frame, img, x, y):
    h, w = frame.shape[:2]; ih, iw = img.shape[:2]
    sx, sy = max(0, x), max(0, y); ex, ey = min(w, x + iw), min(h, y + ih)
    if sx >= ex or sy >= ey: return
    isx, isy = sx - x, sy - y; iex, iey = isx + (ex - sx), isy + (ey - sy)
    if iex > iw or iey > ih: return
    region = img[isy:iey, isx:iex]
    if region.shape[2] == 4:
        alpha = region[:, :, 3:4] / 255.0
        frame[sy:ey, sx:ex] = (frame[sy:ey, sx:ex] * (1 - alpha) + region[:, :, :3] * alpha).astype(np.uint8)
    else:
        frame[sy:ey, sx:ex] = region[:, :, :3]
