# webui.py — Web 配置面板 v2.1
import json, os, sys, subprocess, glob as gmod
from http.server import HTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOB_LOG = []  # 全局生成日志

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        routes = {
            "/api/config": self._send_config,
            "/api/presets": self._send_presets,
            "/api/assets": self._send_asset_list,
            "/api/fonts": self._send_fonts,
            "/api/material-db": self._send_material_db,
            "/api/job-log": self._send_job_log,
            "/api/templates": self._send_templates,
        }
        if self.path in routes:
            routes[self.path]()
        elif self.path in ("/", ""):
            self.path = "/webui.html"; super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path.startswith("/api/upload-"):
            folder = self.path.replace("/api/upload-","")
            m = {"icons":"icons","backgrounds":"backgrounds","bg":"backgrounds",
                 "clips":"clips","clip":"clips","music":"music","bgm":"music","icon":"icons"}
            folder = m.get(folder, folder)
            fname = self.headers.get("X-Filename","uploaded_file")
            d = os.path.join(BASE_DIR,"assets",folder)
            os.makedirs(d,exist_ok=True)
            with open(os.path.join(d,fname),"wb") as f: f.write(body)
            self._json({"ok":True,"path":f"assets/{folder}/{fname}"})
            return

        s = body.decode("utf-8")
        if self.path == "/api/save": self._save_config(s)
        elif self.path == "/api/generate": self._run_generate()
        elif self.path == "/api/reset-icons": self._reset_icons()
        elif self.path == "/api/delete-asset": self._delete_asset(s)
        elif self.path == "/api/scan-assets": self._scan_assets()
        elif self.path == "/api/extract-audio": self._extract_audio(s)
        elif self.path == "/api/apply-template": self._apply_template(s)
        else: self.send_response(404); self.end_headers()

    # ---- Fonts ----
    def _send_fonts(self):
        fonts = []
        for d in [os.path.join(BASE_DIR,"assets","fonts"), "C:/Windows/Fonts"]:
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith(('.ttf','.ttc','.otf')):
                        name = os.path.splitext(f)[0]
                        if any(c > '一' for c in name[:3]):  # has CJK = likely supports Chinese
                            fonts.append({"name":name,"path":os.path.join(d,f),"source":"user" if "assets" in d else "system"})
        # dedupe by name
        seen = set(); uniq = []
        for f in fonts:
            if f["name"] not in seen: seen.add(f["name"]); uniq.append(f)
        self._json(uniq)

    # ---- Material DB ----
    def _send_material_db(self):
        db = self._scan_all_assets()
        self._json(db)

    def _scan_assets(self):
        db = self._scan_all_assets()
        # Also auto-fix config background
        bgs = db.get("backgrounds",[])
        if bgs:
            cfg = self._read_config()
            cfg["assets"]["background"] = os.path.join("assets","backgrounds",bgs[0]["name"])
            self._write_config(cfg)
        self._json({"ok":True,"total":sum(len(v) for v in db.values())})

    def _scan_all_assets(self):
        db = {}
        for folder,exts in [("icons",(".png",".jpg",".jpeg",".webp")),
                             ("backgrounds",(".png",".jpg",".jpeg",".webp",".mp4",".mov")),
                             ("clips",(".mp4",".mov",".avi")),
                             ("music",(".mp3",".wav",".ogg"))]:
            p = os.path.join(BASE_DIR,"assets",folder)
            files = []
            if os.path.isdir(p):
                for f in os.listdir(p):
                    fp = os.path.join(p,f)
                    if os.path.isfile(fp) and f.lower().endswith(exts):
                        files.append({"name":f,"path":os.path.join("assets",folder,f),"size_kb":round(os.path.getsize(fp)/1024,1)})
            db[folder] = files
        return db

    # ---- Job Log ----
    def _send_job_log(self):
        self._json({"lines":JOB_LOG})

    # ---- Config ----
    def _read_config(self):
        with open(os.path.join(BASE_DIR,"config.json"),"r",encoding="utf-8") as f:
            return json.load(f)
    def _write_config(self, data):
        with open(os.path.join(BASE_DIR,"config.json"),"w",encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _send_config(self):
        try: self._json(self._read_config())
        except: self._json({})

    def _send_presets(self):
        self._json([
            {"name":"游戏教程","top_title":"游戏安装教程","hook_text":"今天要介绍的是","target_name":"和平精英密钥透","after_reveal_text":"这个真的很好用"},
            {"name":"AI工具推荐","top_title":"AI工具推荐","hook_text":"最近发现一个超好用的","target_name":"Claude Code Agent","after_reveal_text":"效率直接翻倍"},
            {"name":"影视资源","top_title":"影视资源分享","hook_text":"今天分享一部","target_name":"耀眼 (2025)","after_reveal_text":"开头直接进入重点"},
            {"name":"软件安装","top_title":"软件安装教程","hook_text":"手把手教你安装","target_name":"Adobe Photoshop 2026","after_reveal_text":"全程无坑跟着做就行"},
            {"name":"剪辑素材","top_title":"剪辑素材展示","hook_text":"这期素材合集","target_name":"200GB高质量素材包","after_reveal_text":"拍下随时下载"},
        ])

    def _send_asset_list(self):
        assets = {}
        for folder in ["icons","backgrounds","clips","music"]:
            p = os.path.join(BASE_DIR,"assets",folder)
            assets[folder] = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p,f))] if os.path.isdir(p) else []
        self._json(assets)

    def _save_config(self, body):
        try:
            data = json.loads(body)
            cfg = self._read_config()
            if "texts" in data: cfg["texts"] = data["texts"]
            if "project" in data: cfg["project"].update(data["project"])
            if "assets" in data: cfg["assets"].update(data["assets"])
            self._write_config(cfg)
            self._json({"ok":True})
        except Exception as e:
            self._json({"ok":False,"error":str(e)},400)

    # ---- Generate ----
    def _run_generate(self):
        global JOB_LOG
        JOB_LOG = ["[开始] 正在生成视频..."]
        try:
            python = sys.executable
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.Popen(
                [python, os.path.join(BASE_DIR,"main.py")],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                cwd=BASE_DIR, env=env
            )
            for line in proc.stdout:
                JOB_LOG.append(line.strip())
                if len(JOB_LOG) > 100: JOB_LOG.pop(0)
            proc.wait(timeout=300)
            if proc.returncode == 0:
                JOB_LOG.append("[完成] 视频生成成功！")
                self._json({"ok":True,"output":os.path.join(BASE_DIR,"output","output_intro.mp4")})
            else:
                JOB_LOG.append(f"[失败] 返回码: {proc.returncode}")
                self._json({"ok":False,"error":"\n".join(JOB_LOG[-20:])},500)
        except subprocess.TimeoutExpired:
            JOB_LOG.append("[超时] 生成超过 300 秒")
            self._json({"ok":False,"error":"生成超时"},500)
        except Exception as e:
            JOB_LOG.append(f"[错误] {e}")
            self._json({"ok":False,"error":str(e)},500)

    def _reset_icons(self):
        import shutil
        d = os.path.join(BASE_DIR,"assets","icons")
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d,exist_ok=True)
        from PIL import Image, ImageDraw, ImageFont
        colors = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7DC6F','#BB8FCE','#85C1E9']
        labels = ['教程','工具','影视','素材','课程','软件','资料','游戏','AI','插件']
        font = None
        for fp in ["assets/fonts/chinese_font.ttf","C:/Windows/Fonts/msyh.ttc"]:
            if os.path.exists(fp):
                try: font = ImageFont.truetype(fp,48); break
                except: pass
        for i in range(10):
            img = Image.new('RGBA',(300,300),colors[i]); draw = ImageDraw.Draw(img)
            tw,th = 100,60
            if font:
                bbox = draw.textbbox((0,0),labels[i],font=font); tw,th = bbox[2]-bbox[0],bbox[3]-bbox[1]
            draw.text((150-tw//2,150-th//2),labels[i],fill='white',font=font,stroke_width=2,stroke_fill='black')
            img.save(os.path.join(d,f'item_{i+1:02d}.png'))
        img = Image.new('RGBA',(300,300),'#FFD84D'); draw = ImageDraw.Draw(img)
        draw.text((100,130),'目标',fill='white',font=font,stroke_width=3,stroke_fill='black')
        img.save(os.path.join(d,'target.png'))
        self._json({"ok":True,"count":11})

    def _delete_asset(self, body):
        try:
            d = json.loads(body)
            path = os.path.join(BASE_DIR,"assets",d.get("folder",""),d.get("filename",""))
            if os.path.exists(path): os.remove(path)
            self._json({"ok":True})
        except Exception as e:
            self._json({"ok":False,"error":str(e)},400)

    def _send_templates(self):
        p = os.path.join(BASE_DIR,"templates.json")
        self._json(json.load(open(p,"r",encoding="utf-8")) if os.path.exists(p) else {})

    def _apply_template(self, body):
        try:
            data = json.loads(body)
            name = data.get("name","")
            tpls = json.load(open(os.path.join(BASE_DIR,"templates.json"),"r",encoding="utf-8"))
            if name not in tpls:
                self._json({"ok":False,"error":"模板不存在"},400); return
            t = tpls[name]
            cfg = self._read_config()
            cfg["theme"] = t.get("theme",cfg["theme"])
            cfg["layout"] = t.get("layout",cfg["layout"])
            if "animation" in t: cfg["animation"].update(t["animation"])
            self._write_config(cfg)
            self._json({"ok":True,"template":name})
        except Exception as e:
            self._json({"ok":False,"error":str(e)},400)

    def _extract_audio(self, body):
        try:
            data = json.loads(body)
            video_path = data.get("video_path","")
            if not video_path or not os.path.exists(video_path):
                self._json({"ok":False,"error":"视频文件不存在"},400); return
            out_name = data.get("output_name","extracted_bgm.mp3")
            out_path = os.path.join(BASE_DIR,"assets","music",out_name)
            os.makedirs(os.path.dirname(out_path),exist_ok=True)
            result = subprocess.run(
                ["ffmpeg","-y","-i",video_path,"-vn","-acodec","mp3","-q:a","2",out_path],
                capture_output=True,text=True,timeout=120
            )
            if result.returncode == 0 and os.path.exists(out_path):
                # auto-update config
                cfg = self._read_config()
                cfg["assets"]["bgm"] = "assets/music/" + out_name
                self._write_config(cfg)
                self._json({"ok":True,"path":"assets/music/"+out_name})
            else:
                self._json({"ok":False,"error":result.stderr},500)
        except Exception as e:
            self._json({"ok":False,"error":str(e)},500)

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        for h in ["Access-Control-Allow-Origin","Access-Control-Allow-Methods","Access-Control-Allow-Headers"]:
            self.send_header(h,"*")
        self.end_headers()

    def log_message(self, *a): pass

def main():
    os.chdir(BASE_DIR)
    os.makedirs(os.path.join(BASE_DIR,"output"),exist_ok=True)
    print(f"http://localhost:8888")
    HTTPServer(("127.0.0.1",8888),Handler).serve_forever()

if __name__ == "__main__":
    main()
