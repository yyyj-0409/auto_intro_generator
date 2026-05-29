# modules/export_video.py — 视频导出

import os
import subprocess
from moviepy import CompositeVideoClip, CompositeAudioClip


def export_video(clips_with_timing, config, bgm=None, sfx=None):
    """
    合成并导出最终视频。
    clips_with_timing: [(clip, start_time, end_time), ...]
    """
    width = config["project"]["width"]
    height = config["project"]["height"]
    fps = config["project"]["fps"]
    output_dir = "output"
    output_name = config["project"]["output_name"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_name)

    # 将所有 clip 对齐时间轴
    positioned_clips = []
    for clip, start, end in clips_with_timing:
        duration = end - start
        positioned = clip.with_start(start).with_duration(duration)
        positioned_clips.append(positioned)

    final_video = CompositeVideoClip(positioned_clips, size=(width, height))

    # 音频合成
    audio_clips = []
    if bgm:
        audio_clips.append(bgm)

    if sfx:
        for name, sfx_clip in sfx.items():
            if sfx_clip is None:
                continue
            # 在揭晓时刻放置音效
            if name == "impact" and sfx_clip:
                sfx_clip = sfx_clip.with_start(2.1)
            elif name == "whoosh" and sfx_clip:
                sfx_clip = sfx_clip.with_start(0.0)
            audio_clips.append(sfx_clip)

    if audio_clips:
        try:
            final_audio = CompositeAudioClip(audio_clips)
            final_video = final_video.with_audio(final_audio)
        except Exception as e:
            print(f"警告: 音频合成失败，输出静音视频: {e}")

    # 编码参数
    print(f"正在导出视频到: {output_path}")
    print(f"  分辨率: {width}x{height}")
    print(f"  帧率: {fps}fps")
    print(f"  总时长: {config['project']['duration']}秒")

    final_video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="8000k",
        threads=4,
        logger=None,
    )

    final_video.close()
    return output_path
