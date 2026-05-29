# IntroForge — 短视频开头生成器

> 「图标盲盒抽选 → 爆点揭晓 → 实拍转场」一键生成专业级短视频开头

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-required-green.svg)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

自动生成 **6 秒 1080p@60fps** 短视频片头 MP4。适合教程类、推荐类、展示类视频内容的开场制作。

## 效果演示

```
0.0s ──────────────────────────────────── 6.0s
├─ 图标盲盒高速抽选 + 扫描线 (easeOutBack 缓出)
├─ ★ 目标揭晓: 粒子爆发 + 冲击波 + 光芒放射 + RGB 偏移
├─ 停留展示: 呼吸缩放 + 环绕粒子 + 状态标签
├─ 转场: 速度线 → 白闪 → 缩放模糊
└─ 片尾实拍片段
```

**画质特性**: 电影级暗角 · 胶片颗粒 · Teal & Orange 色彩分级 · 运动模糊 · Cubic-bezier 精确缓动

## 快速开始（本地部署）

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 3.12 |
| FFmpeg | 任意 | 需在 PATH 中 |
| Windows / macOS / Linux | — | 跨平台 |

### 1. 克隆仓库

```bash
git clone https://github.com/yyyj-0409/auto_intro_generator.git
cd auto_intro_generator
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 准备中文字体（Windows 可跳过）

```bash
# Windows 系统已自带中文字体，无需额外操作
# macOS / Linux:
# 将任意中文字体(.ttf/.otf)放入 assets/fonts/chinese_font.ttf
```

### 4. 准备素材（必须）

```
assets/
├── backgrounds/    # 背景图片 (.webp/.png/.jpg)
├── icons/          # 候选图标 (5-10个, .png 推荐)
├── clips/          # intro_clip.mp4 (片尾实拍片段, 必备!)
├── fonts/          # chinese_font.ttf (中文字体)
├── music/          # bgm.mp3 (可选)
└── sfx/            # whoosh.mp3 / impact.mp3 (可选)
```

> **intro_clip.mp4** 是唯一必备文件，没有它生成会失败。放到 `assets/clips/` 下。

### 5. 启动

**Web 面板（推荐）:**

```bash
python webui.py
# 打开 http://localhost:8888
# 5 步工作流: 选模板 → 上传素材 → 配置文案 → 调参数 → 一键生成
```

**命令行:**

```bash
python main.py
# 输出: output/output_intro.mp4
```

### 6. 编辑配置

所有参数通过 Web 面板可视化配置，也可直接编辑 `config.json`:

```json
{
  "project": { "fps": 60, "duration": 6.0 },
  "texts": { "top_title": "你的标题", "target_name": "目标名称" },
  "timing": { "reveal": 2.5, "cut_to_clip": 4.2 },
  "effects": { "particle_burst": { "enabled": true } }
}
```

## 内置模板

| 模板 | 风格 | 适用场景 |
|------|------|----------|
| 游戏安装教程 | 霓虹科技风 | 怀旧游戏、手游、端游 |
| 软件安装教程 | 干净专业风 | Photoshop、PR、插件 |
| AI 工具推荐 | 未来科技风 | ChatGPT、Claude、AI 工具 |
| 影视资源介绍 | 影院暗金风 | 电影、电视剧、纪录片 |
| 素材合集展示 | 高级电商风 | 剪辑素材、模板、音效包 |
| 课程资料展示 | 清爽教育风 | 网课、教程、考证资料 |

## 输出规格

- **分辨率**: 1920×1080 (横屏)
- **帧率**: 60fps
- **时长**: 6.0s (可配置)
- **编码**: H.264 · AAC · MP4
- **码率**: 15Mbps · CRF 17 · preset slow

## 项目结构

```
auto_intro_generator/
├── main.py                 # CLI 入口 (v3.2)
├── webui.py                # Web 面板后端 (HTTP API)
├── webui.html              # Web 面板前端 (毛玻璃 UI)
├── webui.bat               # Windows 自动重启启动器
├── config.json             # 用户配置
├── templates.json          # 6 套模板预设
├── requirements.txt        # Python 依赖
├── modules/
│   ├── effects.py          # 粒子/冲击波/调色/暗角/颗粒/模糊
│   ├── intro_scene.py      # 图标盲盒抽选场景
│   ├── reveal_scene.py     # 目标揭晓场景
│   ├── hold_scene.py       # 停留展示场景
│   ├── text_renderer.py    # 中文字幕渲染
│   ├── asset_loader.py     # 素材加载器
│   ├── config_loader.py    # 配置校验
│   └── export_video.py     # 视频导出
├── assets/                 # 用户素材目录
│   ├── backgrounds/
│   ├── icons/
│   ├── clips/
│   ├── fonts/
│   ├── music/
│   └── sfx/
└── output/                 # 生成输出
```

## 技术栈

- **视频引擎**: moviepy 2.x + FFmpeg (H.264 编码)
- **图像渲染**: Pillow (ImageDraw, ImageFont, ImageFilter)
- **粒子系统**: NumPy 向量化帧渲染
- **Web 面板**: Python http.server + Vanilla JS + CSS Glassmorphism

## 常见问题

**Q: 生成失败提示 "intro_clip 路径错误"？**
A: 确保 `assets/clips/intro_clip.mp4` 存在，且路径在 `config.json` 中正确配置。

**Q: 字幕不显示或乱码？**
A: 检查 `assets/fonts/chinese_font.ttf` 是否存在。Windows 用户会自动使用系统字体微软雅黑。

**Q: 视频没有声音？**
A: 默认不包含音频。将 BGM 放到 `assets/music/bgm.mp3`，音效放到 `assets/sfx/whoosh.mp3` 和 `assets/sfx/impact.mp3`。

**Q: 能部署到服务器吗？**
A: 可以。`webui.py` 是标准 Python HTTP 服务，绑定 `127.0.0.1:8888`。修改 `webui.py` 中的 `server_address` 为 `0.0.0.0` 即可对外服务。生成任务通过子进程异步执行，不阻塞请求。

**Q: 生成速度如何？**
A: 60fps/6s 在 i7+ 机器上约需 30-60 秒（preset=slow, crf=17）。调整 preset 为 `medium` 可加快。
