# 通用短视频开头模板生成器

本地 Python 工具，根据素材自动生成 5-6 秒短视频开头 MP4。风格为"素材盲盒抽选 + 爆点揭晓 + 切入实录"。

## 安装依赖

```bash
pip install -r requirements.txt
```

依赖：
- `moviepy>=2.0` — 视频合成
- `pillow>=10.0` — 字幕渲染
- `numpy>=1.24` — 帧处理

> **Windows 用户**：MoviePy 新版本使用 `moviepy`（无大写），不是旧版 `moviepy`。

## 准备素材

将素材放入 `assets/` 目录：

```
assets/
├── backgrounds/        # 背景图片/视频
│   └── bg.png          # 或 bg.mp4
├── icons/              # 图标/封面图（PNG/JPG/WebP）
│   ├── item_01.png     # 候选图标（至少放几个）
│   ├── item_02.png
│   ├── item_03.png
│   └── target.png      # 目标图标
├── clips/              # 实录视频
│   └── intro_clip.mp4
├── music/              # 背景音乐（可选）
│   └── bgm.mp3
├── sfx/                # 音效（可选）
│   ├── whoosh.mp3      # 滚动音效
│   └── impact.mp3      # 揭晓音效
└── fonts/              # 中文字体（必须）
    └── chinese_font.ttf
```

### 中文字体（重要）

**必须放置中文字体文件**，否则程序会报错。

Windows 可以直接复制系统字体：
```powershell
copy C:\Windows\Fonts\msyh.ttc assets\fonts\chinese_font.ttf
```

或者下载[思源黑体](https://github.com/adobe-fonts/source-han-sans)。

## 修改配置

编辑 `config.json`，主要修改 `texts` 和 `assets` 部分：

```json
{
  "texts": {
    "top_title": "冒险岛下载教程",
    "hook_text": "今天要介绍的是",
    "target_name": "冒险岛国际服 RISE 版本",
    "after_reveal_text": "这个真的很好用"
  },
  "assets": {
    "target_icon": "assets/icons/target.png",
    "intro_clip": "assets/clips/intro_clip.mp4",
    "icons_dir": "assets/icons"
  }
}
```

## 运行

```bash
python main.py
```

输出文件在 `output/output_intro.mp4`。

## 切换主题

换一套素材 + 改 config.json 即可，无需改代码：

| 场景 | 改什么 |
|------|--------|
| 换标题 | `texts.top_title` |
| 换悬念文案 | `texts.hook_text` |
| 换目标名 | `texts.target_name` |
| 换结尾文案 | `texts.after_reveal_text` |
| 换图标 | 替换 `assets/icons/` 里的文件 |
| 换目标图标 | 改 `assets.target_icon` |
| 换实录视频 | 替换 `assets/clips/intro_clip.mp4` |
| 换背景 | 替换 `assets/backgrounds/bg.png` |
| 换 BGM | 替换 `assets/music/bgm.mp3` |
| 自定义分辨率 | 改 `project.width` 和 `project.height` |

## 视频结构

| 时间 | 阶段 | 效果 |
|------|------|------|
| 0.0-2.1s | 图标抽选 | 图标横向滚动，中间固定选择框，顶部标题 + 底部悬念字幕 |
| 2.1-2.5s | 目标揭晓 | 图标放大居中，闪白 + 色差 + 震动冲击 |
| 2.5-4.5s | 目标停留 | 图标居中，呼吸缩放动画，高亮边框 |
| 4.5-6.0s | 切入实录 | 硬切到实录视频，底部情绪字幕 |

## 常见问题

### 报错 "找不到中文字体文件"
把中文字体（.ttf 或 .ttc）放到 `assets/fonts/chinese_font.ttf`。

### 字幕乱码
确保字体文件是支持中文的 TrueType 字体。

### MoviePy 版本问题
如果报 `ModuleNotFoundError: No module named 'moviepy'`：
```bash
pip install moviepy pillow numpy
```

### 生成视频黑屏
检查图标格式是否为 PNG/JPG/WebP，且 `icons_dir` 路径正确。

### 素材缺失不报错
背景、BGM、音效缺失时程序会自动生成替代内容（渐变背景、静音等）。
只有**中文字体**缺失时会明确报错。

### 如何加速生成
在 `config.json` 中可调整 `project.fps` 降低帧率，或减小 `project.duration` 缩短视频。

## 注意事项

- 禁止在默认文案中使用"永久""终身"等字样
- 工具仅限个人使用，不是售卖商品
- 支持 PNG/JPG/WebP 格式图标
- 图标数量少于 5 个时自动循环复制
- 没有 bgm 或音效时正常输出静音视频
- 没有背景时自动生成暗色渐变背景
