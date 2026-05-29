# modules/intro_scene.py — 图标抽选 v2.2: 加速→快扫→减速停目标

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from moviepy import ImageClip, CompositeVideoClip, VideoClip
from modules.effects import create_selector_box, rounded_icon, dark_bg_gradient, ease_out, ease_in_out


def create_roulette_scene(icon_images, target_idx, config, duration):
    """三阶段变速: 0-t1加速 → t1-t2快速 → t2-end减速缓出到target"""
    T = config["timing"]
    t_accel = T["slide_fast"] - T["slide_start"]    # 加速阶段时长
    t_fast = T["slide_slow"] - T["slide_fast"]       # 快速阶段时长
    t_slow = T["reveal"] - T["slide_slow"]           # 减速阶段时长

    width = config["project"]["width"]
    height = config["project"]["height"]
    fps = config["project"]["fps"]
    icon_size = config["animation"]["icon_size"]
    layout = config["layout"]

    box_w = layout["selector_box_width"]
    box_h = layout["selector_box_height"]
    box_y = layout["selector_box_y"]
    box_cx = width // 2
    box_cy = box_y + box_h // 2

    box_img, box_pad = create_selector_box(box_w, box_h, "#FFFFFF", 2, 20)
    box_clip = ImageClip(box_img).with_duration(duration).with_position(
        (box_cx - box_w // 2 - box_pad, box_cy - box_h // 2 - box_pad))

    if not icon_images:
        return VideoClip(lambda t: dark_bg_gradient(width, height), duration=duration)

    round_icons = [rounded_icon(img, 20, shadow=True) for img in icon_images]
    total = len(round_icons)
    avg_iw = sum(a.shape[1] for a in round_icons) / total
    icon_spacing = int(avg_iw * 1.3)

    bg = dark_bg_gradient(width, height)
    n_frames = int(duration * fps)
    frames = []

    # 总滚动量: 让足够多的图标经过选择框
    total_scroll = 3.0  # 抽选期间滚动 3 轮
    max_speed = total_scroll / max(0.01, t_fast + t_accel * 0.5)  # 快速期速度

    for fi in range(n_frames):
        t = fi / fps
        frame = bg.copy()

        if t <= t_accel:
            # 阶段1: 加速 (ease_in)
            p = t / t_accel
            eased = p * p  # 二次加速
            offset = eased * max_speed * t_accel * 0.5
        elif t <= t_accel + t_fast:
            # 阶段2: 匀速快扫
            offset_start = max_speed * t_accel * 0.5
            offset = offset_start + max_speed * (t - t_accel)
        else:
            # 阶段3: 减速缓出到 target_idx
            p = min(1.0, (t - t_accel - t_fast) / max(0.01, t_slow))
            eased = ease_out(p)
            offset_start = max_speed * t_accel * 0.5 + max_speed * t_fast
            offset = offset_start + (target_idx - offset_start % total) * eased
            if offset < offset_start:
                offset += total * max(1, int((offset_start - offset) / total))

        offset = offset % total

        num_visible = (width // icon_spacing) + 6
        start_icon = int(offset) - num_visible // 2

        for i in range(start_icon, start_icon + num_visible):
            idx = i % total
            if idx < 0: idx += total
            arr = round_icons[idx]
            ih, iw = arr.shape[:2]
            cx = int(box_cx + (i - offset) * icon_spacing - iw // 2)
            if cx + iw < -100 or cx > width + 100: continue

            dist = abs(cx + iw // 2 - box_cx)
            perspective = max(0.7, 1.0 - min(1.0, dist / (width * 0.6)) * 0.3)
            opacity = max(0.3, 1.0 - min(1.0, dist / (width * 0.6)) * 0.7)
            bright = 1.25 if dist < box_w // 2 + iw // 4 else opacity

            sw, sh = max(20, int(iw * perspective)), max(20, int(ih * perspective))
            scaled = _resize(arr, sw, sh)
            px, py = cx + (iw - sw) // 2, int(box_cy - sh // 2)
            _paste(frame, scaled, px, py, bright)

        frames.append(frame)

    def make_frame(t):
        return frames[min(int(t * fps), n_frames - 1)]

    fg = VideoClip(make_frame, duration=duration)
    return CompositeVideoClip([fg, box_clip], size=(width, height))


_resize_cache = {}
def _resize(arr, w, h):
    key = (id(arr) % 100000, w, h)
    if key not in _resize_cache:
        _resize_cache[key] = np.array(Image.fromarray(arr).resize((w, h), Image.LANCZOS))
    return _resize_cache[key]


def _paste(frame, icon, x, y, brightness):
    h, w = frame.shape[:2]; ih, iw = icon.shape[:2]
    sx, sy = max(0, x), max(0, y); ex, ey = min(w, x + iw), min(h, y + ih)
    if sx >= ex or sy >= ey: return
    isx, isy = sx - x, sy - y; iex, iey = isx + (ex - sx), isy + (ey - sy)
    if iex > iw or iey > ih: return
    region = icon[isy:iey, isx:iex]
    if region.shape[2] != 4: return
    alpha = region[:, :, 3:4] / 255.0
    rgb = np.clip(region[:, :, :3].astype(np.float32) * brightness, 0, 255).astype(np.uint8)
    frame[sy:ey, sx:ex] = (frame[sy:ey, sx:ex] * (1 - alpha) + rgb * alpha).astype(np.uint8)
