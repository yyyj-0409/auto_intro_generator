# modules/config_loader.py — 加载和验证 config.json

import json
import os

def load_config(config_path="config.json"):
    """加载并验证配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}\n请在项目根目录创建 config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 验证必要字段
    required_sections = ["project", "theme", "texts", "assets", "timing", "animation", "layout"]
    for sec in required_sections:
        if sec not in config:
            raise KeyError(f"config.json 缺少必要字段: {sec}")

    # 检查禁用词
    forbidden_words = ["永久", "终身"]
    for key in ["top_title", "hook_text", "target_name", "after_reveal_text"]:
        text = config["texts"].get(key, "")
        for word in forbidden_words:
            if word in text:
                raise ValueError(f"texts.{key} 中出现了禁止使用的词汇: '{word}'，请使用中性表达")

    # 展开相对路径
    base_dir = os.path.dirname(os.path.abspath(config_path))
    for asset_key in ["background", "target_icon", "intro_clip", "bgm",
                       "whoosh_sfx", "impact_sfx", "font", "icons_dir"]:
        path = config["assets"].get(asset_key, "")
        if path and not os.path.isabs(path):
            config["assets"][asset_key] = os.path.join(base_dir, path)

    return config


def validate_assets(config):
    """验证素材是否存在，返回缺失列表"""
    missing = []
    assets_to_check = {
        "background": "背景素材",
        "target_icon": "目标图标",
        "intro_clip": "实录视频",
        "icons_dir": "图标文件夹",
    }

    for key, label in assets_to_check.items():
        path = config["assets"].get(key, "")
        if path and not os.path.exists(path):
            missing.append(f"{label}: {path}")

    # font 特别检查
    font_path = config["assets"].get("font", "")
    if font_path and not os.path.exists(font_path):
        missing.append(
            f"中文字体文件: {font_path}\n"
            f"  请将中文字体文件（如微软雅黑 msyh.ttc 或思源黑体）复制到 assets/fonts/ 目录"
        )

    # icons_dir 检查
    icons_dir = config["assets"].get("icons_dir", "")
    if icons_dir and os.path.isdir(icons_dir):
        icons = [f for f in os.listdir(icons_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if not icons and not os.path.exists(config["assets"].get("target_icon", "")):
            missing.append(f"图标文件夹为空且没有目标图标: {icons_dir}")

    return missing
