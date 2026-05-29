#!/usr/bin/env python
# main.py — v3.2 6.0s 短视频开头生成器

import sys, os, numpy as np
from PIL import Image

if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass
    try: os.system("chcp 65001 > nul")
    except: pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.config_loader import load_config, validate_assets
from modules.asset_loader import load_icons, load_background, load_audio, load_intro_clip, load_icon_images
from modules.text_renderer import render_text_clip_animated
from modules.intro_scene import create_roulette_scene
from modules.reveal_scene import create_reveal_scene
from modules.hold_scene import create_hold_scene
from modules.effects import dark_bg_gradient, make_speed_lines_frame, make_zoom_blur_frame


def main():
    print("=" * 50)
    print("  短视频开头生成器 v3.2")
    print("=" * 50)

    # 1
    config = load_config("config.json")
    T = config["timing"]
    L = config["layout"]
    W, H = config["project"]["width"], config["project"]["height"]
    FPS = config["project"]["fps"]
    TD = T["end"]
    icon_size = config["animation"]["icon_size"]
    target_size = 480
    show_sub = config["project"].get("subtitle_enabled", True)

    print(f"\n[1/6] 配置: {config['texts']['target_name']} | {W}x{H}@{FPS}fps | {TD}s")
    missing = validate_assets(config)
    if missing:
        for m in missing: print(f"  ⚠️  {m}")

    # 2 — Load all assets
    print("\n[2/6] 加载素材...")
    icon_files, target_idx = load_icons(config["assets"]["icons_dir"], config["assets"]["target_icon"])
    icon_images = load_icon_images(icon_files, icon_size)
    target_icon_idx = target_idx % len(icon_images) if target_idx >= 0 and icon_images else 0
    print(f"  图标: {len(icon_images)} | 目标索引: {target_icon_idx}")

    # Background (Bug fix: 真正参与合成)
    bg_path = config["assets"]["background"]
    background = load_background(bg_path, W, H, TD, FPS)
    print(f"  背景: {'已加载' if bg_path and os.path.exists(bg_path) else '使用默认渐变'}")

    # Target image (high-res)
    tp = config["assets"]["target_icon"]
    if tp and os.path.exists(tp):
        target_image = np.array(Image.open(tp).convert("RGBA"))
        print(f"  目标图标: {os.path.basename(tp)}")
    elif icon_images:
        target_image = icon_images[target_icon_idx]
        print(f"  目标图标: 使用第{target_icon_idx}个图标")
    else:
        target_image = None
        print("  ⚠️ 无目标图标")

    # Intro clip (Bug fix: 硬性检查)
    intro_path = config["assets"]["intro_clip"]
    if not intro_path or not os.path.exists(intro_path):
        print(f"  ❌ intro_clip 路径错误: {intro_path}")
        print("  请确认文件存在并重新运行。")
        sys.exit(1)
    intro_clip = load_intro_clip(intro_path, W, H)
    if intro_clip is None:
        print(f"  ❌ intro_clip 加载失败: {intro_path}")
        sys.exit(1)
    print(f"  ✅ intro_clip: {os.path.basename(intro_path)}")

    # Audio
    bgm, sfx = load_audio(
        config["assets"]["bgm"],
        {"whoosh": config["assets"]["whoosh_sfx"], "impact": config["assets"]["impact_sfx"]},
        TD
    )
    for name in ["whoosh", "impact"]:
        p = config["assets"].get(f"{'whoosh_sfx' if name=='whoosh' else 'impact_sfx'}", "")
        if not p or not os.path.exists(p):
            print(f"  ⚠️ 缺少音效: {name} — 跳过")
    print(f"  BGM: {'已加载' if bgm else '静音'}")

    # 3 — Subtitles
    print(f"\n[3/6] 字幕 ({'(跳过)' if not show_sub else '动画'})...")
    from moviepy import ColorClip
    def _sub(effect, edur, text, size, color, stroke, sw, dur, pos_y):
        if not show_sub or not text:
            return ColorClip((1, 1), color=(0, 0, 0, 0)).with_duration(0)
        c, _, _ = render_text_clip_animated(text, size, color, stroke, sw, dur, effect, edur)
        return c.with_position(("center", pos_y))

    title_clip  = _sub("fade_in", 0.4, config["texts"]["top_title"], 68,
                       "#FFFFFF", "#000000", 5, T["cut_to_clip"], L["top_title_y"])
    hook_clip   = _sub("typewriter", 1.0, config["texts"]["hook_text"], 60,
                       "#CCCCCC", "#000000", 4, T["reveal"], L["bottom_text_y"])
    target_clip = _sub("scale_in", 0.25, config["texts"]["target_name"], 82,
                       config["theme"]["highlight_color"], "#000000", 5,
                       TD - T["reveal"], L["bottom_text_y"])
    target_clip = target_clip.with_start(T["reveal"])
    after_clip  = _sub("slide_up", 0.25, config["texts"]["after_reveal_text"], 64,
                       "#FFFFFF", "#000000", 4, TD - T["cut_to_clip"], L["bottom_text_y"])
    after_clip = after_clip.with_start(T["cut_to_clip"])
    print("  ✅ 字幕完成")

    # 4 — Scenes
    print("\n[4/6] 场景合成...")

    # Roulette (slide_start → reveal)
    roulette_dur = T["reveal"] - T["slide_start"]
    roulette = create_roulette_scene(icon_images, target_icon_idx, config, roulette_dur)
    print(f"  抽选: {T['slide_start']}-{T['reveal']}s ({roulette_dur}s)")

    # Reveal (reveal → reveal_end)
    reveal_dur = T["reveal_end"] - T["reveal"]
    reveal = create_reveal_scene(target_image, config, reveal_dur)
    print(f"  揭晓: {T['reveal']}-{T['reveal_end']}s ({reveal_dur}s)")

    # Hold (hold_start → cut_to_clip)
    hold_dur = T["cut_to_clip"] - T["hold_start"]
    hold = create_hold_scene(target_image, config, hold_dur)
    print(f"  停留: {T['hold_start']}-{T['cut_to_clip']}s ({hold_dur}s)")

    # Intro clip (cut_to_clip → end)
    clip_dur = TD - T["cut_to_clip"]
    cut_clip = intro_clip.subclipped(0, min(clip_dur, intro_clip.duration))
    print(f"  实录: {T['cut_to_clip']}-{TD}s ({clip_dur}s)")

    # 0.1s flash transition at cut point
    from moviepy import VideoClip as VC
    flash_frames = []
    flash_dur = 0.1
    for fi in range(int(flash_dur * FPS)):
        t = fi / FPS
        progress = t / flash_dur
        frame = np.ones((H, W, 3), dtype=np.uint8) * int(255 * (1.0 - progress))
        flash_frames.append(frame)
    def flash_make(t):
        i = min(int(t * FPS), len(flash_frames) - 1) if flash_frames else 0
        return flash_frames[i] if flash_frames else np.ones((H, W, 3), dtype=np.uint8) * 255
    flash_trans = VC(flash_make, duration=flash_dur).with_start(T["cut_to_clip"])

    # 速度线过渡 (cut_to_clip 前 0.15s, 逐渐增强)
    tr_cfg = config.get("effects", {}).get("transition_speed_lines", {})
    if tr_cfg.get("enabled", True):
        sl_dur = tr_cfg.get("duration", 0.15)
        sl_start = T["cut_to_clip"] - sl_dur
        sl_frames = []
        for fi in range(int(sl_dur * FPS)):
            t_sl = fi / FPS
            sl_frame = make_speed_lines_frame(W, H, t_sl, sl_dur, direction="radial")
            sl_frames.append(sl_frame[:, :, :3])
        def speed_line_make(t):
            i = min(int(t * FPS), len(sl_frames) - 1) if sl_frames else 0
            return sl_frames[i]
        speed_line_overlay = VC(speed_line_make, duration=sl_dur).with_start(sl_start)
    else:
        speed_line_overlay = ColorClip((1, 1), color=(0, 0, 0, 0)).with_duration(0)

    # 缩放模糊过渡 (cut_to_clip 后 0.15s, 柔化硬切到实录)
    zb_cfg = config.get("effects", {}).get("transition_zoom_blur", {})
    if zb_cfg.get("enabled", True):
        zb_dur = zb_cfg.get("duration", 0.15)
        zb_frames = []
        for fi in range(int(zb_dur * FPS)):
            t_zb = fi / FPS
            zb_frame = make_zoom_blur_frame(W, H, t_zb, zb_dur)
            zb_frames.append(zb_frame[:, :, :3])
        def zoom_blur_make(t):
            i = min(int(t * FPS), len(zb_frames) - 1) if zb_frames else 0
            return zb_frames[i]
        zoom_blur_overlay = VC(zoom_blur_make, duration=zb_dur).with_start(T["cut_to_clip"])
    else:
        zoom_blur_overlay = ColorClip((1, 1), color=(0, 0, 0, 0)).with_duration(0)

    # 5 — Composite (Bug fix: background FIRST)
    print("\n[5/6] 合成...")
    all_clips = [
        background.with_start(0).with_duration(TD),
        roulette.with_start(0).with_duration(roulette_dur),
        reveal.with_start(T["reveal"]).with_duration(reveal_dur),
        hold.with_start(T["hold_start"]).with_duration(hold_dur),
        speed_line_overlay,           # 速度线 (cut 前 0.15s)
        flash_trans,                  # 白闪 (cut 时刻)
        zoom_blur_overlay,            # 缩放模糊 (cut 后 0.15s)
        cut_clip.with_start(T["cut_to_clip"]).with_duration(clip_dur),
        title_clip.with_duration(T["cut_to_clip"]),
        hook_clip.with_duration(T["reveal"]),
        target_clip,
        after_clip,
    ]

    # 6 — Export
    print("\n[6/6] 导出...")
    output_path = export_hq(all_clips, config, bgm, sfx, W, H, FPS, TD, T)
    print(f"\n{'='*50}\n  ✅ 完成!\n  📁 {os.path.abspath(output_path)}\n{'='*50}")


def export_hq(clips, config, bgm, sfx, W, H, FPS, TD, T):
    from moviepy import CompositeVideoClip, CompositeAudioClip
    os.makedirs("output", exist_ok=True)
    out = os.path.join("output", config["project"]["output_name"])

    final = CompositeVideoClip(clips, size=(W, H))

    # Audio with proper error reporting
    audio_clips = []
    if bgm:
        audio_clips.append(bgm.with_duration(TD).with_volume(0.2))
    for name, s in (sfx or {}).items():
        if s is None: continue
        pos = {"whoosh": T["slide_start"], "impact": T["reveal"]}.get(name, 0)
        audio_clips.append(s.with_start(pos).with_volume(0.6))

    has_audio = len(audio_clips) > 0
    if has_audio:
        try:
            final = final.with_audio(CompositeAudioClip(audio_clips))
        except Exception as e:
            print(f"  ❌ 音频合成失败: {e}")

    # Info
    print(f"  分辨率: {W}x{H}  |  FPS: {FPS}  |  时长: {TD}s  |  音频: {'有' if has_audio else '无'}  |  preset=slow crf=17")

    final.write_videofile(
        out, fps=FPS, codec="libx264", audio_codec="aac" if has_audio else None,
        preset="slow", bitrate="15000k", audio_bitrate="256k",
        ffmpeg_params=["-crf", "17"], threads=8, logger=None
    )
    final.close()
    return out


if __name__ == "__main__":
    main()
