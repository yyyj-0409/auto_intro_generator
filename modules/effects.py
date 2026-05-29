# modules/effects.py — 视觉效果 + 粒子系统 + 转场

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ==================== 电影级背景 ====================

def _simplex_noise_2d(width, height, scale=80.0, seed=42):
    """纯 numpy 实现的简化 Perlin 风格噪声纹理"""
    np.random.seed(seed)
    # 生成低频随机网格
    gx = width // scale + 2
    gy = height // scale + 2
    grid = np.random.randn(gy, gx, 2)
    # 归一化梯度
    norm = np.sqrt(grid[:, :, 0]**2 + grid[:, :, 1]**2) + 1e-10
    grid[:, :, 0] /= norm
    grid[:, :, 1] /= norm

    # 生成坐标
    xs = np.linspace(0, gx - 1, width)
    ys = np.linspace(0, gy - 1, height)

    result = np.zeros((height, width), dtype=np.float32)
    for octave in range(3):
        freq = 2 ** octave
        amp = 1.0 / freq
        ox = (xs * freq) % (gx - 2)
        oy = (ys * freq) % (gy - 2)

        ix = ox.astype(int)
        iy = oy.astype(int)
        fx = (ox - ix).reshape(1, -1)
        fy = (oy - iy).reshape(-1, 1)

        # 四角梯度点积
        g00 = grid[iy[:, None], ix, 0] * fx + grid[iy[:, None], ix, 1] * fy
        g10 = grid[iy[:, None], ix + 1, 0] * (fx - 1) + grid[iy[:, None], ix + 1, 1] * fy
        g01 = grid[iy[:, None] + 1, ix, 0] * fx + grid[iy[:, None] + 1, ix, 1] * (fy - 1)
        g11 = grid[iy[:, None] + 1, ix + 1, 0] * (fx - 1) + grid[iy[:, None] + 1, ix + 1, 1] * (fy - 1)

        # 平滑插值
        sx = fx * fx * (3 - 2 * fx)
        sy = fy * fy * (3 - 2 * fy)
        v0 = g00 + sx * (g10 - g00)
        v1 = g01 + sx * (g11 - g01)
        result += amp * (v0 + sy * (v1 - v0))

    # 归一化到 0-1
    result = (result - result.min()) / (result.max() - result.min() + 1e-10)
    return result


def dark_bg_gradient(width, height):
    """电影级暗黑背景：渐变 + 噪声纹理 + 暗角 + 光斑"""
    frame = np.zeros((height, width, 3), dtype=np.float32)

    # 基础渐变: 深蓝 → 深紫
    for y in range(height):
        t = y / height
        r = 4 + 22 * t + 6 * (1 - abs(t - 0.5) * 2)
        g = 2 + 12 * t
        b = 12 + 35 * (1 - t * 0.7)
        frame[y, :, 0] = np.clip(r, 0, 255)
        frame[y, :, 1] = np.clip(g, 0, 255)
        frame[y, :, 2] = np.clip(b, 0, 255)

    # 噪声纹理叠加
    noise = _simplex_noise_2d(width, height, scale=100, seed=42)
    noise2 = _simplex_noise_2d(width, height, scale=50, seed=99)
    noise_combined = (noise * 0.6 + noise2 * 0.4)

    for c in range(3):
        frame[:, :, c] += noise_combined * 15 * (0.5 + c * 0.3)

    # 暗角 (Vignette)
    cx, cy = width // 2, height // 2
    y_grid, x_grid = np.ogrid[:height, :width]
    dist = np.sqrt(((x_grid - cx) / (width * 0.65))**2 + ((y_grid - cy) / (height * 0.65))**2)
    vignette = np.clip(1.0 - dist * 0.6, 0.3, 1.0)
    for c in range(3):
        frame[:, :, c] *= vignette

    # 随机光斑（向量化）
    np.random.seed(77)
    spots = [(np.random.randint(width//6, 5*width//6),
              np.random.randint(height//6, 5*height//6),
              np.random.randint(80, 200),
              [[180,160,220],[200,180,240],[255,220,180],[140,160,200]][np.random.randint(0,4)])
             for _ in range(4)]

    y_idx, x_idx = np.ogrid[:height, :width]
    for sx, sy, sr, color in spots:
        dx = (x_idx - sx).astype(np.float32) / sr
        dy = (y_idx - sy).astype(np.float32) / sr
        dist = np.sqrt(dx**2 + dy**2)
        mask = dist < 1
        alpha = ((1 - dist) ** 2 * 0.08) * mask
        for c in range(3):
            frame[:, :, c] += alpha * color[c]

    return np.clip(frame, 0, 255).astype(np.uint8)


# ==================== 粒子系统 (Task 5) ====================

def create_particle_burst(cx, cy, num=25, max_radius=400, duration=0.4):
    """粒子爆发轨迹预计算"""
    np.random.seed(42)
    angles = np.random.uniform(0, 2 * np.pi, num)
    speeds = np.random.uniform(0.5, 1.0, num)
    sizes = np.random.uniform(2, 6, num)
    # 暖色粒子 (金色→白色)
    color_pool = [[255, 220, 100], [255, 240, 180], [255, 255, 220], [255, 200, 80], [220, 180, 220]]
    colors = [color_pool[np.random.randint(0, 5)] for _ in range(num)]
    max_dist = max_radius * speeds
    return {
        'cx': cx, 'cy': cy, 'angles': angles, 'speeds': speeds,
        'sizes': sizes, 'colors': colors, 'max_dist': max_dist,
        'duration': duration
    }


def create_shockwave_ring(cx, cy, max_radius=600, duration=0.3):
    """环形冲击波预计算"""
    return {'cx': cx, 'cy': cy, 'max_radius': max_radius, 'duration': duration}


def create_light_rays(cx, cy, num_rays=10, max_length=500, duration=0.3):
    """光芒放射预计算"""
    angles = np.linspace(0, 2 * np.pi, num_rays, endpoint=False) + np.random.uniform(0, 0.5, num_rays)
    return {'cx': cx, 'cy': cy, 'angles': angles, 'max_length': max_length, 'duration': duration}


def create_orbiting_particles(cx, cy, num=4, orbit_radius=250, duration=2.0):
    """环绕粒子预计算"""
    angles = np.linspace(0, 2 * np.pi, num, endpoint=False)
    speeds = np.random.uniform(0.5, 1.5, num)
    sizes = np.random.uniform(1.5, 3.5, num)
    return {'cx': cx, 'cy': cy, 'angles': angles, 'speeds': speeds,
            'sizes': sizes, 'orbit_radius': orbit_radius, 'duration': duration}


def render_particle_burst(frame, t, burst_data):
    """将粒子爆发渲染到帧上"""
    d = burst_data
    if t < 0 or t > d['duration']:
        return
    progress = t / d['duration']
    for i in range(len(d['angles'])):
        dist = progress * d['max_dist'][i]
        alpha = 1.0 - progress
        if alpha <= 0:
            continue
        px = int(d['cx'] + np.cos(d['angles'][i]) * dist)
        py = int(d['cy'] + np.sin(d['angles'][i]) * dist)
        r = int(d['sizes'][i])
        y1, y2 = max(0, py - r), min(frame.shape[0], py + r + 1)
        x1, x2 = max(0, px - r), min(frame.shape[1], px + r + 1)
        if y2 <= y1 or x2 <= x1:
            continue
        color = np.array(d['colors'][i], dtype=np.float32)
        frame[y1:y2, x1:x2] = (frame[y1:y2, x1:x2] * (1 - alpha * 0.7)
                                + color * alpha * 0.7).astype(np.uint8)


def render_shockwave(frame, t, sw_data):
    """渲染冲击波环"""
    d = sw_data
    if t < 0 or t > d['duration']:
        return
    progress = t / d['duration']
    radius = int(progress * d['max_radius'])
    alpha = 1.0 - progress
    thickness = max(1, int(3 + 6 * alpha))

    for r_offset in range(-thickness, thickness + 1):
        r = radius + r_offset
        if r < 10:
            continue
        a = alpha * 0.4 * (1 - abs(r_offset) / (thickness + 1))
        _draw_ring(frame, d['cx'], d['cy'], r, a, [255, 220, 100])


def render_light_rays(frame, t, ray_data):
    """渲染光芒放射"""
    d = ray_data
    if t < 0 or t > d['duration']:
        return
    progress = t / d['duration']
    length = progress * d['max_length']
    alpha = 1.0 - progress
    if alpha <= 0:
        return

    for angle in d['angles']:
        ex = int(d['cx'] + np.cos(angle) * length)
        ey = int(d['cy'] + np.sin(angle) * length)
        sx, sy = int(d['cx']), int(d['cy'])

        # 画简单三角形（宽度随距离递减）
        w = int(3 + 8 * alpha)
        for pw in range(-w, w + 1):
            a2 = alpha * 0.3 * (1 - abs(pw) / (w + 1))
            px = int(ex + np.cos(angle + np.pi / 2) * pw)
            py = int(ey + np.sin(angle + np.pi / 2) * pw)

            # 画线从中心到端点
            steps = max(1, int(length / 3))
            for j in range(steps):
                ix = int(sx + (px - sx) * j / steps)
                iy = int(sy + (py - sy) * j / steps)
                if 0 <= iy < frame.shape[0] and 0 <= ix < frame.shape[1]:
                    color = np.array([255, 235, 180], dtype=np.float32)
                    frame[iy, ix] = (frame[iy, ix] * (1 - a2) + color * a2).astype(np.uint8)


def render_orbiting_particles(frame, t, orbit_data):
    """渲染环绕粒子"""
    d = orbit_data
    if t < 0 or t > d['duration']:
        return
    for i in range(len(d['angles'])):
        angle = d['angles'][i] + t * d['speeds'][i] * 2 * np.pi
        px = int(d['cx'] + np.cos(angle) * d['orbit_radius'])
        py = int(d['cy'] + np.sin(angle) * d['orbit_radius'])
        r = int(d['sizes'][i])
        y1, y2 = max(0, py - r), min(frame.shape[0], py + r + 1)
        x1, x2 = max(0, px - r), min(frame.shape[1], px + r + 1)
        if y2 <= y1 or x2 <= x1:
            continue
        color = np.array([255, 220, 130], dtype=np.float32)
        alpha = 0.6
        frame[y1:y2, x1:x2] = (frame[y1:y2, x1:x2] * (1 - alpha)
                                + color * alpha).astype(np.uint8)


def _draw_ring(frame, cx, cy, radius, alpha, color):
    """画一个环形"""
    h, w = frame.shape[:2]
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    mask = np.abs(dist - radius) < 1.5
    if np.any(mask):
        for c in range(3):
            frame[mask, c] = (frame[mask, c] * (1 - alpha)
                              + color[c] * alpha).astype(np.uint8)


# ==================== HUD/商业级 UI ====================

def create_hud_frame(w, h, accent="#7C5CFF", glow_strength=0.55):
    """HUD 风格扫描框: 四角短线 + 发光"""
    pad = 35
    tw, th = w + pad * 2, h + pad * 2
    img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = _hex_to_rgb(accent)
    glow = int(255 * glow_strength)

    # 外发光
    for i in range(5, 0, -1):
        draw.rounded_rectangle(
            [pad - i * 3, pad - i * 3, pad + w + i * 3, pad + h + i * 3],
            radius=18 + i, fill=(c[0], c[1], c[2], int(glow / i * 0.6)))

    # 主体边框
    draw.rounded_rectangle([pad, pad, pad + w, pad + h], radius=18,
                           fill=(c[0], c[1], c[2], 10), outline=tuple(c), width=2)

    # 四角短线装饰
    cl = 35  # corner length
    cw = 3
    corners = [(pad, pad), (pad + w - cl, pad), (pad, pad + h - cl), (pad + w - cl, pad + h - cl)]
    for cx, cy in corners:
        draw.rounded_rectangle([cx, cy, cx + cl, cy + cw], radius=2, fill=tuple(c))
        draw.rounded_rectangle([cx, cy, cx + cw, cy + cl], radius=2, fill=tuple(c))

    return np.array(img), pad


def create_glass_card(img_array, radius=16, border_color="#FFFFFF"):
    """玻璃拟态图标卡片: 圆角 + 阴影 + 细边框 + 半透底"""
    h, w = img_array.shape[:2]
    card = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    # 投影
    for i in range(6, 0, -1):
        a = int(30 / i)
        draw.rounded_rectangle([6 + i, 6 + i + 3, w + 14 + i, h + 14 + i + 3],
                               radius=radius + i, fill=(0, 0, 0, a))
    # 半透底色
    draw.rounded_rectangle([6, 6, w + 14, h + 14], radius=radius,
                           fill=(255, 255, 255, 15), outline=border_color, width=1)
    # 贴图
    icon = Image.fromarray(img_array)
    card.paste(icon, (10, 10), icon)
    return np.array(card)


def draw_scan_line(frame, t, duration=0.2, y_range=None):
    """横向扫描线: 从顶部扫到底部"""
    h, w = frame.shape[:2]
    if y_range is None:
        y_range = (h // 4, h * 3 // 4)
    progress = min(1.0, t / duration)
    y = int(y_range[0] + (y_range[1] - y_range[0]) * progress)
    alpha = 0.3 if progress < 0.5 else 0.3 * (2 - 2 * progress)
    color = np.array([255, 255, 255], dtype=np.float32)
    y1, y2 = max(0, y - 2), min(h, y + 3)
    if y2 > y1:
        frame[y1:y2, :] = (frame[y1:y2, :] * (1 - alpha) + color * alpha).astype(np.uint8)


def draw_status_badge(frame, text, x, y, t, duration=0.3):
    """状态标签: LOCKED/READY"""
    if t < 0 or t > duration: return
    alpha = min(1.0, t / 0.1) if t < duration / 2 else max(0, 1 - (t - duration / 2) / (duration / 2))
    font = None
    for fp in ["assets/fonts/chinese_font.ttf", "C:/Windows/Fonts/msyh.ttc"]:
        if os.path.exists(fp):
            try: font = ImageFont.truetype(fp, 28); break
            except: pass
    if font is None: return
    badge = Image.new("RGBA", (200, 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(badge)
    d.rounded_rectangle([0, 0, 199, 49], radius=10, fill=(124, 92, 255, int(200 * alpha)))
    d.text((20, 8), text, font=font, fill=(255, 255, 255, int(255 * alpha)))
    badge_arr = np.array(badge)
    bh, bw = badge_arr.shape[:2]
    sx, sy = max(0, x - bw // 2), max(0, y - bh // 2)
    _overlay_rgba(frame, badge_arr, sx, sy)


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _overlay_rgba(frame, overlay, x, y):
    h, w = frame.shape[:2]; oh, ow = overlay.shape[:2]
    sx, sy = max(0, x), max(0, y); ex, ey = min(w, x + ow), min(h, y + oh)
    if sx >= ex or sy >= ey: return
    region = overlay[sy - y:ey - y, sx - x:ex - x]
    if region.shape[2] == 4:
        alpha = region[:, :, 3:4] / 255.0
        frame[sy:ey, sx:ex] = (frame[sy:ey, sx:ex] * (1 - alpha) + region[:, :, :3] * alpha).astype(np.uint8)


# ==================== UI 元素 ====================

def create_selector_box(w, h, border_color="#FFFFFF", border_width=2, radius=20, pulsing=False, pulse_time=0):
    """圆角选择框 + 外发光，支持脉动"""
    pad = 30
    total_w, total_h = w + pad * 2, h + pad * 2
    img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 脉动系数
    glow_mult = 1.0
    if pulsing and pulse_time > 0:
        glow_mult = 0.6 + 0.4 * abs(np.sin(pulse_time * np.pi * 1.5))

    for i in range(6, 0, -1):
        glow_alpha = int(80 / i * glow_mult)
        r = radius + i * 3
        draw.rounded_rectangle(
            [pad - i * 2, pad - i * 2, pad + w + i * 2, pad + h + i * 2],
            radius=r, fill=(255, 255, 255, glow_alpha))

    draw.rounded_rectangle(
        [pad, pad, pad + w, pad + h], radius=radius,
        fill=(255, 255, 255, 8), outline=border_color, width=border_width)

    # 四角加强
    corner_len, corner_w = 30, 3
    for dx, dy in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
        for sx, sy in [(pad, pad), (pad + w - corner_len, pad),
                        (pad, pad + h - corner_len), (pad + w - corner_len, pad + h - corner_len)]:
            draw.rounded_rectangle(
                [sx - dx, sy - dy, sx + corner_len - dx, sy + corner_w - dy],
                radius=2, fill=border_color)
            draw.rounded_rectangle(
                [sx - dx, sy - dy, sx + corner_w - dx, sy + corner_len - dy],
                radius=2, fill=border_color)

    return np.array(img), pad


def rounded_icon(img_array, radius=24, shadow=True):
    """圆角裁切 + 投影"""
    h, w = img_array.shape[:2]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    mask_arr = np.array(mask, dtype=np.uint8)

    if img_array.shape[2] == 4:
        result = img_array.copy()
        alpha_ch = result[:, :, 3]
        result[:, :, 3] = (alpha_ch.astype(np.float32) * mask_arr.astype(np.float32) / 255.0).astype(np.uint8)
    else:
        result = np.zeros((h, w, 4), dtype=np.uint8)
        result[:, :, :3] = img_array[:, :, :3]
        result[:, :, 3] = mask_arr

    if shadow:
        result = _add_shadow(result, radius)
    return result


def _add_shadow(img_array, radius):
    """柔和投影"""
    h, w = img_array.shape[:2]
    pad = 30
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for i in range(8, 0, -1):
        alpha = int(40 / i)
        draw.rounded_rectangle(
            [pad + i, pad + i + 4, pad + w - i, pad + h - i + 4],
            radius=radius + i, fill=(0, 0, 0, alpha))
    canvas.paste(Image.fromarray(img_array), (pad, pad), Image.fromarray(img_array))
    return np.array(canvas)


# ==================== 视觉特效 ====================

def flash_frame(frame, t, flash_start, flash_duration=0.15, peak_alpha=180, radial=False):
    """闪白效果（支持径向）"""
    if t < flash_start - 0.08 or t > flash_start + flash_duration + 0.08:
        return frame.copy()
    if t < flash_start:
        progress = (t - (flash_start - 0.08)) / 0.08
    elif t < flash_start + flash_duration:
        progress = 1.0
    else:
        progress = 1.0 - (t - flash_start - flash_duration) / 0.08
    progress = max(0, min(1, progress))

    if radial:
        h, w = frame.shape[:2]
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - w / 2)**2 + (y - h / 2)**2) / (max(w, h) * 0.5)
        radial_falloff = np.clip(1 - dist, 0.3, 1.0)
        alpha_map = (progress * peak_alpha / 255.0) * radial_falloff[:, :, None]
        result = (frame * (1 - alpha_map) + 255 * alpha_map).astype(np.uint8)
    else:
        white = np.ones_like(frame, dtype=np.uint8) * 255
        alpha = progress * (peak_alpha / 255.0)
        result = (frame * (1 - alpha) + white * alpha).astype(np.uint8)
    return result


def rgb_shift(frame, t, shift_start, shift_duration=0.2, max_shift=4):
    if t < shift_start or t > shift_start + shift_duration:
        return frame.copy()
    progress = (t - shift_start) / shift_duration
    shift = int(max_shift * (1 - abs(progress - 0.5) * 2))
    if shift <= 0:
        return frame.copy()
    h, w = frame.shape[:2]
    result = frame.copy()
    result[:, :w - shift, 2] = frame[:, shift:, 2]
    result[:, shift:, 0] = frame[:, :w - shift, 0]
    return result


def breathing_scale(t, start_t, end_t, min_scale=0.95, max_scale=1.05, freq=1.5):
    if t < start_t or t > end_t:
        return 1.0
    progress = (t - start_t) / max(0.001, end_t - start_t)
    wave = np.sin(t * freq * np.pi * 2) * 0.5 + 0.5
    if progress > 0.8:
        wave *= 1.0 - (progress - 0.8) / 0.2
    return min_scale + (max_scale - min_scale) * wave


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3

def ease_in_out(t):
    if t < 0.5: return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2

def cubic_bezier_ease_out_back(t):
    """cubic-bezier(0.22, 0.61, 0.36, 1.0) — 抽选减速"""
    if t <= 0: return 0
    if t >= 1: return 1
    return 1 + 2.7 * (t - 1) ** 3 + 1.7 * (t - 1) ** 2

def cubic_bezier_bounce(t):
    """cubic-bezier(0.34, 1.56, 0.64, 1.0) — 揭晓弹跳"""
    if t <= 0: return 0
    if t >= 1: return 1
    return 1 + 3.9 * (t - 1) ** 3 + 2.9 * (t - 1) ** 2

def add_film_grain(frame, strength=0.06):
    """胶片颗粒"""
    h, w = frame.shape[:2]
    noise = np.random.randn(h, w, 1) * 15 * strength
    return np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)

def color_grade(frame, shadow_blue=5, mid_warm=3, contrast=1.05):
    """电影调色: 暗部偏蓝, 微增对比"""
    f = frame.astype(np.float32)
    mask = (f.mean(axis=2) < 60).astype(np.float32)
    f[:, :, 2] += mask * shadow_blue
    mid = ((f.mean(axis=2) > 40) & (f.mean(axis=2) < 180)).astype(np.float32)
    f[:, :, 0] += mid * mid_warm
    f = (f - 128) * contrast + 128
    return np.clip(f, 0, 255).astype(np.uint8)

def apply_motion_blur(img_arr, strength=3):
    """水平运动模糊"""
    if strength <= 1: return img_arr
    k = int(strength); result = np.zeros_like(img_arr, dtype=np.float32)
    for o in range(k):
        s = o - k // 2
        shifted = img_arr.copy()
        if s > 0: shifted = np.roll(shifted, s, axis=1)
        elif s < 0: shifted = np.roll(shifted, -abs(s), axis=1)
        result += shifted.astype(np.float32) / k
    return np.clip(result, 0, 255).astype(np.uint8)

def draw_vignette(frame, strength=0.4):
    """增强暗角"""
    h, w = frame.shape[:2]
    y, x = np.ogrid[:h, :w]
    d = np.sqrt(((x - w // 2) / (w * 0.6))**2 + ((y - h // 2) / (h * 0.6))**2)
    v = np.clip(1.0 - d * strength, 0.6, 1.0)
    return np.clip(frame.astype(np.float32) * v[:, :, None], 0, 255).astype(np.uint8)


# ==================== 转场 (Task 7) ====================

def make_speed_lines_frame(width, height, t, duration, direction="radial"):
    """生成单帧速度线效果"""
    frame = np.zeros((height, width, 4), dtype=np.float32)
    progress = min(1.0, t / duration) if duration > 0 else 1.0
    alpha = 1.0 - progress

    np.random.seed(55)
    num_lines = 30

    if direction == "radial":
        cx, cy = width // 2, height // 2
        for i in range(num_lines):
            angle = 2 * np.pi * i / num_lines + np.random.uniform(-0.2, 0.2)
            length = min(width, height) * (0.3 + progress * 0.7)
            ex = int(cx + np.cos(angle) * length)
            ey = int(cy + np.sin(angle) * length)
            sx, sy = cx, cy
            _draw_line_aa(frame, sx, sy, ex, ey, [255, 255, 255], alpha * 0.6)
    else:
        for i in range(num_lines):
            y = np.random.randint(0, height)
            length = width * (0.3 + progress * 0.7) * np.random.uniform(0.5, 1.0)
            sx = np.random.randint(0, width)
            _draw_line_aa(frame, sx, y, int(sx + length), y, [255, 255, 255], alpha * 0.5)

    return frame


def make_zoom_blur_frame(width, height, t, duration, zoom_factor=1.3):
    """缩放模糊过渡帧：中心清晰，边缘向外拉伸"""
    progress = min(1.0, t / duration) if duration > 0 else 1.0
    alpha = progress  # 逐渐覆盖
    frame = np.zeros((height, width, 4), dtype=np.float32)

    # 径向模糊条
    cx, cy = width // 2, height // 2
    np.random.seed(66)
    for i in range(40):
        angle = 2 * np.pi * i / 40
        length = min(width, height) * 0.4 * progress
        ex = int(cx + np.cos(angle) * length)
        ey = int(cy + np.sin(angle) * length)
        _draw_line_aa(frame, cx, cy, ex, ey, [200, 200, 255], alpha * 0.3)

    return frame


def _draw_line_aa(frame, x1, y1, x2, y2, color, alpha):
    """简单抗锯齿画线"""
    h, w = frame.shape[:2]
    steps = max(1, int(np.sqrt((x2 - x1)**2 + (y2 - y1)**2)))
    for j in range(steps + 1):
        t = j / max(1, steps)
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        if 0 <= y < h and 0 <= x < w:
            frame[y, x, :3] += np.array(color) * alpha
            frame[y, x, 3] = alpha
