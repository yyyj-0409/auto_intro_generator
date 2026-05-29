# IntroForge — 短视频开头生成器

> 「素材盲盒抽选 · 爆点揭晓 · 一键生成」

本地创作工具，可用于个人内容生产。自动生成 4.8 秒短视频开头 MP4。

## 适用场景

游戏安装教程 / 软件安装教程 / AI 工具推荐 / 影视资源展示 / 素材合集展示 / 课程资料展示

## 安装

```bash
pip install -r requirements.txt
```

**Windows 用户**：需确保已安装 FFmpeg 且在 PATH 中。

## 中文字体

将中文字体放入 `assets/fonts/chinese_font.ttf`，或使用 Windows 系统字体：

```powershell
copy C:\Windows\Fonts\msyh.ttc assets\fonts\chinese_font.ttf
```

## 启动

### Web 面板（推荐）

```bash
python webui.py
```

打开 http://localhost:8888 ，按 5 步完成：选模板 → 上传素材 → 配置文案 → 调参数 → 生成。

### 命令行

```bash
python main.py
```

## 模板

内置 6 个专业模板，一键切换：

- 游戏安装教程 — 霓虹科技风
- 软件安装教程 — 干净专业风
- AI 工具推荐 — 未来科技风
- 影视资源介绍 — 影院暗金风
- 素材合集展示 — 高级电商风
- 课程资料展示 — 清爽教育风

## 输出规格

- 分辨率：横屏 1920×1080 / 竖屏 1080×1920 / 方形 1080×1080
- 帧率：30 / 60fps
- 编码：H.264 · AAC · MP4
- 时长：4.8s（默认）/ 6.0s

## 项目结构

```
auto_intro_generator/
├── main.py              # CLI 入口
├── webui.py             # Web 面板后端
├── webui.html           # Web 面板前端
├── config.json          # 用户配置
├── templates.json       # 6 个模板预设
├── modules/             # 生成引擎
│   ├── effects.py       # 视觉效果
│   ├── intro_scene.py   # 抽选场景
│   ├── reveal_scene.py  # 揭晓场景
│   ├── hold_scene.py    # 停留场景
│   └── ...
├── assets/              # 用户素材
└── output/              # 输出视频
```

## 常见问题

**生成失败？** 检查 intro_clip 是否存在于 assets/clips/，中文字体是否就位。

**字幕乱码？** 确保中文字体文件是 TrueType 格式且放在正确位置。

**视频太慢？** 建议日常使用 30fps，最终版使用 60fps。
