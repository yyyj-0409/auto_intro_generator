# modules/hold_scene.py — v2.2 短暂停留: 1.00-1.04微呼吸

import numpy as np
from PIL import Image
from moviepy import ImageClip, VideoClip, CompositeVideoClip
from modules.effects import (
    create_selector_box, rounded_icon, dark_bg_gradient,
    breathing_scale,
    create_orbiting_particles, render_orbiting_particles,
    draw_scan_line, draw_status_badge,
    apply_post_processing,
)


def create_hold_scene(target_image, config, duration):
    width = config["project"]["width"]
    height = config["project"]["height"]
    fps = config["project"]["fps"]
    target_size = 480

    if target_image is None:
        target_image = np.ones((target_size, target_size, 4), dtype=np.uint8) * [60, 60, 100, 255]

    polished = rounded_icon(target_image, 24, shadow=True)
    target_arr = np.array(Image.fromarray(polished))

    box_w, box_h = 540, 540
    cx, cy = width // 2, height // 2 - 30
    box_img, box_pad = create_selector_box(box_w, box_h, "#FFD84D", 2, 24)
    box_clip = ImageClip(box_img).with_duration(duration).with_position(
        (cx - box_w // 2 - box_pad, cy - box_h // 2 - box_pad))

    # 预计算环绕粒子
    eff_cfg = config.get("effects", {})
    if eff_cfg.get("orbiting_particles", {}).get("enabled", True):
        orbit = create_orbiting_particles(
            cx, cy,
            num=eff_cfg["orbiting_particles"].get("count", 5),
            orbit_radius=eff_cfg["orbiting_particles"].get("orbit_radius", 280),
            duration=duration)
    else:
        orbit = None

    bg = dark_bg_gradient(width, height)
    n_frames = int(duration * fps)
    frames = []

    for fi in range(n_frames):
        t = fi / fps
        frame = bg.copy()
        scale = breathing_scale(t, 0.0, duration, 0.98, 1.04, 1.5)

        sz = max(10, int(target_size * scale))
        scaled = np.array(Image.fromarray(target_arr).resize((sz, sz), Image.LANCZOS))
        sx, sy = cx - sz // 2, cy - sz // 2
        _paste(frame, scaled, sx, sy)

        # 环绕粒子
        if orbit is not None:
            render_orbiting_particles(frame, t, orbit)

        # 扫描线 (前半段扫过一次)
        if eff_cfg.get("hold_scan_line", {}).get("enabled", True):
            scan_dur = eff_cfg["hold_scan_line"].get("duration", 0.4)
            if t < scan_dur:
                draw_scan_line(frame, t, duration=scan_dur)

        # 状态标签 (开头闪现)
        if eff_cfg.get("status_badge", {}).get("enabled", True):
            badge_dur = 0.6
            if t < badge_dur:
                draw_status_badge(
                    frame,
                    eff_cfg["status_badge"].get("text", "READY"),
                    width // 2, height - 120, t, badge_dur)

        # 全局后处理
        frame = apply_post_processing(frame, config)
        frames.append(frame)

    def make_frame(t):
        return frames[min(int(t * fps), n_frames - 1)]

    fg = VideoClip(make_frame, duration=duration)
    return CompositeVideoClip([fg, box_clip], size=(width, height))


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
