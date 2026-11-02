import os, glob, shutil, tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app, expose_headers=["Content-Disposition"])
HEIGHTS = [2160, 1440, 1080, 720, 480, 360]

def opts(extra=None):
    o = {"quiet": True, "noplaylist": True}
    if os.path.exists("cookies.txt"):
        o["cookiefile"] = "cookies.txt"
    o.update(extra or {})
    return o

@app.get("/health")
def health():
    return "ok"

@app.get("/info")
def info():
    url = request.args.get("url", "")
    try:
        with yt_dlp.YoutubeDL(opts({"skip_download": True})) as y:
            d = y.extract_info(url, download=False)
    except Exception as e:
        return jsonify(error=str(e)[:200]), 400
    have = [f.get("height") or 0 for f in d.get("formats", [])]
    fm = [{"id": "best", "label": "Best"}]
    fm += [{"id": "h%d" % h, "label": "%dp" % h} for h in HEIGHTS if any(x >= h for x in have)]
    fm.append({"id": "audio", "label": "Audio MP3"})
    return jsonify(title=d.get("title"), thumbnail=d.get("thumbnail"), formats=fm)

@app.get("/download")
def download():
    url = request.args.get("url", "")
    f = request.args.get("f", "best")
    tmp = tempfile.mkdtemp()
    out = tmp + "/%(title).80s.%(ext)s"
    if f == "audio":
        o = opts({"format": "bestaudio/best", "outtmpl": out,
                  "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]})
    else:
        h = f[1:] if f.startswith("h") and f[1:].isdigit() else None
        c = "[height<=%s]" % h if h else ""
        fmt = "bv*%s[vcodec^=avc1]+ba[ext=m4a]/bv*%s+ba/b%s" % (c, c, c)
        o = opts({"format": fmt, "merge_output_format": "mp4", "outtmpl": out})
    try:
        with yt_dlp.YoutubeDL(o) as y:
            y.download([url])
        path = glob.glob(tmp + "/*")[0]
    except Exception as e:
        shutil.rmtree(tmp, True)
        return jsonify(error=str(e)[:200]), 400
    resp = send_file(path, as_attachment=True)
    resp.call_on_close(lambda: shutil.rmtree(tmp, True))
    return resp
  
