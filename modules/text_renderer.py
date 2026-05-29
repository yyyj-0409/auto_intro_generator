# modules/text_renderer.py — 中文字幕渲染 + 动画

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, VideoClip


def _load_font(size):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_paths = [
        os.path.join(base, "assets", "fonts", "chinese_font.ttf"),
        os.path.join(base, "assets", "fonts", "chinese_font.otf"),
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    raise FileNotFoundError(f"找不到中文字体！已尝试: {font_paths}")


def render_text_clip(text, font_size=52, color="#FFFFFF", stroke_color="#000000",
                     stroke_width=3, duration=5, position="center"):
    """渲染文字为带描边的透明 PNG ImageClip。返回 (clip, width, height)"""
    font = _load_font(font_size)
    dummy_img = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(dummy_img).textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    pad = stroke_width * 4
    img_w, img_h = text_w + pad * 2, text_h + pad * 2
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.text((pad + dx, pad + dy), text, font=font, fill=stroke_color)
    draw.text((pad, pad), text, font=font, fill=color)

    clip = ImageClip(np.array(img)).with_duration(duration)
    return clip, img_w, img_h


def render_text_clip_animated(text, font_size=52, color="#FFFFFF", stroke_color="#000000",
                               stroke_width=3, duration=5, effect="none",
                               effect_duration=0.5):
    """
    带动画效果的文字渲染。
    effect: "none" / "fade_in" / "typewriter" / "scale_in" / "slide_up"
    """
    font = _load_font(font_size)
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy.textbbox((0, 0), text, font=font)
    full_w, full_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = stroke_width * 4
    img_w, img_h = full_w + pad * 2, full_h + pad * 2

    if effect == "none":
        return render_text_clip(text, font_size, color, stroke_color, stroke_width, duration)

    # 预渲染完整文字
    full_img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(full_img)
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                fdraw.text((pad + dx, pad + dy), text, font=font, fill=stroke_color)
    fdraw.text((pad, pad), text, font=font, fill=color)
    full_arr = np.array(full_img)

    def make_frame(t):
        if effect == "fade_in":
            progress = min(1.0, t / effect_duration) if effect_duration > 0 else 1.0
            result = full_arr.copy().astype(np.float32)
            result[:, :, 3] *= progress
            return result.astype(np.uint8)

        elif effect == "typewriter":
            progress = min(1.0, t / effect_duration) if effect_duration > 0 else 1.0
            char_count = max(1, int(len(text) * progress))
            partial = text[:char_count]
            return _render_static_text(partial, font, img_w, img_h, pad, fdraw,
                                       color, stroke_color, stroke_width)

        elif effect == "scale_in":
            progress = min(1.0, t / effect_duration) if effect_duration > 0 else 1.0
            ease = 1 - (1 - progress) ** 3
            scale = 0.5 + 0.5 * ease
            if scale < 0.01:
                scale = 0.01
            sw, sh = max(1, int(img_w * scale)), max(1, int(img_h * scale))
            scaled = np.array(Image.fromarray(full_arr).resize((sw, sh), Image.LANCZOS))
            # 居中放置
            ox, oy = (img_w - sw) // 2, (img_h - sh) // 2
            result = np.zeros((img_h, img_w, 4), dtype=np.uint8)
            if ox >= 0 and oy >= 0 and ox + sw <= img_w and oy + sh <= img_h:
                result[oy:oy+sh, ox:ox+sw] = scaled
            result[:, :, 3] = (result[:, :, 3].astype(np.float32) * ease).astype(np.uint8)
            return result

        elif effect == "slide_up":
            progress = min(1.0, t / effect_duration) if effect_duration > 0 else 1.0
            ease = 1 - (1 - progress) ** 3
            offset = int(img_h * 0.5 * (1 - ease))
            result = np.zeros((img_h, img_w, 4), dtype=np.uint8)
            sy = max(0, offset)
            copy_h = min(img_h - sy, img_h)
            if copy_h > 0:
                result[sy:sy+copy_h, :] = full_arr[:copy_h, :]
            result[:, :, 3] = (result[:, :, 3].astype(np.float32) * ease).astype(np.uint8)
            return result

        return full_arr

    clip = VideoClip(make_frame, duration=duration)
    return clip, img_w, img_h


def _render_static_text(text, font, img_w, img_h, pad, draw_obj, color, stroke_color, stroke_width):
    """渲染静态文字（用于打字机效果）"""
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                d.text((pad + dx, pad + dy), text, font=font, fill=stroke_color)
    d.text((pad, pad), text, font=font, fill=color)
    return np.array(img)
