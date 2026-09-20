import os
import io
import zipfile
import random
import string
from flask import Flask, request, render_template_string, jsonify, session, redirect, url_for, send_file
from unixgram import Bot, ApiError
from db import init_db, add_code, check_code, is_verified, get_verified_user, check_login

app = Flask(__name__)
app.secret_key = os.urandom(24)
init_db()

BOT_TOKEN = "3193529251:YwHD3tqh47Wd7hs7Ru2mHDoaME5puZxQ"
bot = Bot(BOT_TOKEN)

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verify Bot</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 2l2.5 10.5L28 16l-9.5 3.5L16 30l-2.5-10.5L4 16l9.5-3.5z' fill='%23a78bfa'/%3E%3Cpath d='M24 4l1 4 4 1-4 1-1 4-1-4-4-1 4-1z' fill='%23ec4899'/%3E%3C/svg%3E">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
*:focus{outline:none}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a12;color:#ccc;min-height:100vh;overflow-x:hidden}
canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0}
.wrap{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90%;max-width:380px;z-index:1}
h1{font-size:20px;font-weight:600;color:#eee;margin-bottom:4px}
.sub{color:#555;font-size:13px;margin-bottom:32px}
.lbl{font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#555;margin-bottom:8px}
.desc{color:#666;font-size:13px;margin-bottom:14px}
.field input{width:100%;padding:12px 14px;border:1px solid rgba(255,255,255,.12);border-radius:6px;background:rgba(34,34,34,.7);color:#ddd;font-size:16px;outline:none;font-family:inherit;transition:all .12s;-webkit-appearance:none}
.field input:focus{border-color:rgba(255,255,255,.25);background:rgba(40,40,40,.85)}
.field input::placeholder{color:#555}
.btn{width:100%;padding:12px 20px;border:1px solid rgba(255,255,255,.12);border-radius:6px;background:rgba(34,34,34,.7);color:#aaa;font-size:14px;font-weight:500;cursor:pointer;font-family:inherit;margin-top:10px;transition:all .12s;position:relative;overflow:hidden;-webkit-appearance:none}
.btn::after{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:#a78bfa;opacity:0;transition:opacity .12s}
.btn:hover{background:rgba(40,40,40,.85);border-color:rgba(255,255,255,.2);color:#ddd}
.btn:hover::after{opacity:1}
.btn:active{transform:scale(.98)}
.code-display{background:rgba(255,255,255,.04);border:1px solid #222;border-radius:6px;padding:16px;text-align:center;margin-top:14px;display:none}
.code-val{font-size:28px;font-weight:600;letter-spacing:8px;color:#a78bfa;font-family:'SF Mono','Fira Code',monospace;word-break:break-all}
.code-hint{color:#ddd;font-size:12px;margin-top:10px}
.code-hint b{color:#fff}
.divider{display:flex;align-items:center;gap:10px;margin:24px 0;color:#888;font-size:11px;letter-spacing:1px;text-transform:uppercase}
.divider::before,.divider::after{content:'';flex:1;height:1px;background:rgba(255,255,255,.06)}
.msg{padding:10px;border-radius:6px;text-align:center;font-size:13px;margin-top:10px;display:none}
.msg-ok{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);color:#4a8}
.msg-err{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.2);color:#a55}
@media(max-width:420px){
.wrap{width:92%;max-width:none;padding:0 4px}
h1{font-size:18px}
.code-val{font-size:22px;letter-spacing:6px}
}</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="wrap">
<h1>Verify Bot</h1>
<p class="sub">unixgram verification</p>

<div class="lbl">Step 1</div>
<div class="desc">Enter your unixgram username</div>
<div class="field"><input type="text" id="username" placeholder="username" autocomplete="off"></div>
<button class="btn" onclick="getCode()">Get code</button>
<div class="code-display" id="codeBox">
<div class="code-val" id="codeVal"></div>
<div class="code-hint">Send to bot: <b>/verify CODE</b></div>
</div>
<div class="msg msg-err" id="userErr" style="display:none">User not found</div>

<div class="divider">or</div>

<div class="lbl">Step 2</div>
<div class="desc">Already verified? Log in</div>
<div class="field"><input type="text" id="loginUser" placeholder="username" autocomplete="off"></div>
<div class="field"><input type="password" id="loginPass" placeholder="password" autocomplete="off"></div>
<button class="btn" onclick="doLogin()">Log in</button>
<div class="msg msg-ok" id="okMsg">Logged in</div>
<div class="msg msg-err" id="errMsg">Not verified</div>

</div>
<script>
const gl=document.getElementById('c').getContext('webgl');
let mx=0.5,my=0.5;
document.addEventListener('mousemove',e=>{mx=e.clientX/window.innerWidth;my=1-e.clientY/window.innerHeight});

const vs='attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}';
const fs=`precision mediump float;
uniform float t;uniform vec2 m;uniform vec2 r;
void main(){
vec2 uv=gl_FragCoord.xy/r;
float d=distance(uv,m);
float cellSize=20.0;
vec2 grid=uv*r;
vec2 snapped=floor(grid/cellSize)*cellSize+cellSize*0.5;
vec2 cell=fract(grid/cellSize);
float lineX=smoothstep(0.0,0.04,cell.x)*smoothstep(0.0,0.04,1.0-cell.x);
float lineY=smoothstep(0.0,0.04,cell.y)*smoothstep(0.0,0.04,1.0-cell.y);
float line=1.0-lineX*lineY;
vec3 c=vec3(0.04,0.03,0.08);
float glow=exp(-d*4.0)*0.8;
c+=vec3(0.25,0.1,0.5)*glow;
float cellGlow=exp(-distance(snapped/r,m)*3.0)*0.3;
c+=vec3(0.3,0.15,0.6)*cellGlow;
c+=vec3(0.08,0.05,0.12)*line;
gl_FragColor=vec4(c,1.0);}`;

function sh(t,src){const s=gl.createShader(t);gl.shaderSource(s,src);gl.compileShader(s);return s;}
const pg=gl.createProgram();gl.attachShader(pg,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pg,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pg);gl.useProgram(pg);

const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);

const ut=gl.getUniformLocation(pg,'t'),um=gl.getUniformLocation(pg,'m'),ur=gl.getUniformLocation(pg,'r');

function frame(t){
gl.viewport(0,0,gl.canvas.width,gl.canvas.height);
gl.uniform1f(ut,t/1000);
gl.uniform2f(um,mx,my);
gl.uniform2f(ur,gl.canvas.width,gl.canvas.height);
gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
requestAnimationFrame(frame);
}
function resize(){gl.canvas.width=window.innerWidth;gl.canvas.height=window.innerHeight;}
window.addEventListener('resize',resize);resize();requestAnimationFrame(frame);

async function getCode(){
  const u=document.getElementById('username').value.trim();if(!u)return;
  document.getElementById('userErr').style.display='none';
  document.getElementById('codeBox').style.display='none';
  const r=await fetch('/api/code',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u})});
  const d=await r.json();
  if(d.code){document.getElementById('codeVal').textContent=d.code;document.getElementById('codeBox').style.display='block';document.getElementById('loginUser').value=u}
  else{document.getElementById('userErr').style.display='block'}
}
async function doLogin(){
  const u=document.getElementById('loginUser').value.trim();
  const p=document.getElementById('loginPass').value.trim();
  if(!u||!p)return;
  const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});
  const d=await r.json();
  if(d.ok){window.location.href='/dashboard'}
  else{document.getElementById('errMsg').style.display='block';document.getElementById('okMsg').style.display='none'}
}
</script>
</body>
</html>"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
*:focus{outline:none}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a12;color:#ccc;min-height:100vh;overflow-x:hidden}
canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:0}
.wrap{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:90%;max-width:460px;z-index:1}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px}
.topbar h2{font-size:16px;font-weight:600;color:#eee}
.topbar .logout{color:#555;font-size:12px;text-decoration:none}
.topbar .logout:hover{color:#a55}
.user-block{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:24px;margin-bottom:14px}
.user-block .uname{font-size:18px;font-weight:600;color:#eee;margin-bottom:8px}
.user-block .badge{display:inline-block;font-size:11px;padding:3px 10px;border-radius:4px;background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);color:#4a8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px}
.stat{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:16px}
.stat .k{font-size:11px;color:#444;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.stat .v{font-size:16px;font-weight:500;color:#ddd}
.list{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;padding:20px}
.list h4{font-size:11px;color:#555;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.list li{list-style:none;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:13px;color:#888}
.list li:last-child{border:none}
.download{display:block;text-align:center;padding:12px;border:1px solid rgba(167,139,250,.2);border-radius:6px;color:#a78bfa;font-size:13px;text-decoration:none;margin-top:14px;transition:all .12s}
.download:hover{background:rgba(167,139,250,.08);border-color:rgba(167,139,250,.4);color:#c4b5fd}
@media(max-width:420px){
.wrap{width:92%;max-width:none;padding:0 4px}
.topbar h2{font-size:14px}
.user-block .uname{font-size:16px}
}</style>
</head>
<body>
<canvas id="c"></canvas>
<div class="wrap">
<div class="topbar"><h2>Verify Bot</h2><a href="/logout" class="logout">logout</a></div>
<div class="user-block">
<div class="uname">@{{ username }}</div>
<div class="badge">verified</div>
</div>
<div class="grid">
<div class="stat"><div class="k">Status</div><div class="v">Active</div></div>
<div class="stat"><div class="k">Platform</div><div class="v">Unixgram</div></div>
</div>
<div class="list">
<h4>Features</h4>
<ul>
<li>Account verification</li>
<li>Status check</li>
<li>Group bot access</li>
</ul>
</div>
<a href="/download" class="download">Download source</a>
</div>
<script>
const gl=document.getElementById('c').getContext('webgl');
let mx=0.5,my=0.5;
document.addEventListener('mousemove',e=>{mx=e.clientX/window.innerWidth;my=1-e.clientY/window.innerHeight});
const vs='attribute vec2 p;void main(){gl_Position=vec4(p,0,1);}';
const fs=`precision mediump float;
uniform float t;uniform vec2 m;uniform vec2 r;
void main(){
vec2 uv=gl_FragCoord.xy/r;
float d=distance(uv,m);
float cellSize=20.0;
vec2 grid=uv*r;
vec2 snapped=floor(grid/cellSize)*cellSize+cellSize*0.5;
vec2 cell=fract(grid/cellSize);
float lineX=smoothstep(0.0,0.04,cell.x)*smoothstep(0.0,0.04,1.0-cell.x);
float lineY=smoothstep(0.0,0.04,cell.y)*smoothstep(0.0,0.04,1.0-cell.y);
float line=1.0-lineX*lineY;
vec3 c=vec3(0.04,0.03,0.08);
float glow=exp(-d*4.0)*0.8;
c+=vec3(0.25,0.1,0.5)*glow;
float cellGlow=exp(-distance(snapped/r,m)*3.0)*0.3;
c+=vec3(0.3,0.15,0.6)*cellGlow;
c+=vec3(0.08,0.05,0.12)*line;
gl_FragColor=vec4(c,1.0);}`;
function sh(t,src){const s=gl.createShader(t);gl.shaderSource(s,src);gl.compileShader(s);return s;}
const pg=gl.createProgram();gl.attachShader(pg,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pg,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pg);gl.useProgram(pg);
const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const p=gl.getAttribLocation(pg,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
const ut=gl.getUniformLocation(pg,'t'),um=gl.getUniformLocation(pg,'m'),ur=gl.getUniformLocation(pg,'r');
function frame(t){gl.viewport(0,0,gl.canvas.width,gl.canvas.height);gl.uniform1f(ut,t/1000);gl.uniform2f(um,mx,my);gl.uniform2f(ur,gl.canvas.width,gl.canvas.height);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(frame);}
function resize(){gl.canvas.width=window.innerWidth;gl.canvas.height=window.innerHeight;}
window.addEventListener('resize',resize);resize();requestAnimationFrame(frame);
</script>
</body>
</html>"""

@app.route("/")
def index():
    if "user" in session:
        return redirect("/dashboard")
    return render_template_string(LOGIN_PAGE)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template_string(DASHBOARD_PAGE, username=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

@app.route("/download")
def download():
    if "user" not in session:
        return redirect("/")
    base = os.path.dirname(os.path.abspath(__file__))
    files = ["bot.py", "site.py", "db.py", "requirements.txt", "Dockerfile"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            path = os.path.join(base, f)
            if os.path.exists(path):
                zf.write(path, f)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name="verify-bot.zip")

@app.route("/api/code", methods=["POST"])
def api_code():
    data = request.json
    username = data.get("username", "").strip().lstrip("@")
    if not username:
        return jsonify({"error": "no username"}), 400
    try:
        chat = bot.get_chat(f"@{username}")
        if not chat or not getattr(chat, "username", None):
            return jsonify({"error": "user not found"}), 404
    except (ApiError, Exception):
        return jsonify({"error": "user not found"}), 404
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    add_code(username, code)
    return jsonify({"code": code, "username": username})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").strip().lstrip("@")
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"ok": False})
    if check_login(username, password):
        session["user"] = username
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/api/check/<username>")
def api_check(username):
    user = get_verified_user(username.strip().lstrip("@"))
    return jsonify({"verified": user is not None})

def is_verified_by_username(username):
    user = get_verified_user(username)
    return user is not None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
