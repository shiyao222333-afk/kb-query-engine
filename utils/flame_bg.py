"""
像素火焰横幅 - 可靠版本
直接用 st.markdown + unsafe_allow_html 注入 Canvas + JS
"""

import streamlit as st
import streamlit.components.v1 as components


def render_flame_banner(height: int = 100):
    """
    在 Streamlit 页面中渲染像素火焰横幅
    使用 components.html 渲染（在 iframe 中，可靠）
    """
    # 注意：JS 代码中的 { 和 } 需要用双重大括号转义
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #0E1117;
                overflow: hidden;
            }}
            canvas {{
                display: block;
                width: 100%;
                height: {height}px;
            }}
        </style>
    </head>
    <body>
        <canvas id="c" width="1600" height="{height}"></canvas>
        <script>
            var canvas = document.getElementById('c');
            var ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth || 1600;
            canvas.height = {height};
            var W = canvas.width, H = canvas.height, PX = 8;
            var COLS = Math.floor(W / PX), ROWS = Math.floor(H / PX);
            var fire = [];
            for (var x = 0; x < COLS; x++) {{
                fire[x] = [];
                for (var y = 0; y < ROWS; y++) {{
                    fire[x][y] = 0;
                }}
            }}
            var palette = [];
            for (var i = 0; i < 64; i++) palette.push([i*4, 0, 0]);
            for (var i = 0; i < 64; i++) palette.push([255, i*4, 0]);
            for (var i = 0; i < 64; i++) palette.push([255, 128+i*2, i*4]);
            for (var i = 0; i < 64; i++) palette.push([255, 255, 128+i*2]);
            
            function waveFlame(t) {{
                for (var x = 0; x < COLS; x++) {{
                    for (var y = 0; y < ROWS; y++) {{
                        fire[x][y] = 0;
                    }}
                }}
                for (var x = 0; x < COLS; x++) {{
                    var nx = x / COLS;
                    var wave = (Math.sin(nx * Math.PI * 3 + t * 0.003) * 0.5 + Math.sin(nx * Math.PI * 7 + t * 0.005) * 0.3 + Math.sin(nx * Math.PI * 1.5 + t * 0.001) * 0.2) * 0.5 + 0.5;
                    var h = Math.floor(wave * ROWS * 0.8);
                    for (var y = ROWS - 1; y >= ROWS - h; y--) {{
                        var dy = ROWS - 1 - y;
                        var it = Math.floor((1 - dy / h) * 255 * (0.7 + Math.random() * 0.3));
                        fire[x][y] = Math.min(255, Math.max(0, it));
                    }}
                }}
            }}
            
            function draw() {{
                ctx.fillStyle = 'rgba(14,17,23,0.1)';
                ctx.fillRect(0, 0, W, H);
                for (var x = 0; x < COLS; x++) {{
                    for (var y = 0; y < ROWS; y++) {{
                        if (fire[x][y] > 0) {{
                            var idx = Math.min(255, Math.floor(fire[x][y]));
                            var r = palette[idx][0], g = palette[idx][1], b = palette[idx][2];
                            ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
                            ctx.fillRect(x * PX, y * PX, PX - 1, PX - 1);
                        }}
                    }}
                }}
            }}
            
            var frame = 0;
            function animate() {{
                frame++;
                waveFlame(frame);
                draw();
                requestAnimationFrame(animate);
            }}
            animate();
            
            window.addEventListener('resize', function() {{
                canvas.width = canvas.offsetWidth || 1600;
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html, height=height+20)


def render_flame_sidebar():
    """在侧边栏底部渲染一个小火焰动画"""
    html = """
    <div style="width: 100%; height: 60px; margin-top: 20px;">
        <canvas id="sidebar-flame" width="300" height="60" style="width: 100%; height: 60px;"></canvas>
    </div>
    <script>
        var c = document.getElementById('sidebar-flame');
        if (c) {
            var ctx = c.getContext('2d');
            c.width = c.offsetWidth || 300;
            c.height = 60;
            var W = c.width, H = 60, PX = 6;
            var COLS = Math.floor(W / PX), ROWS = Math.floor(H / PX);
            var fire = [];
            for (var x = 0; x < COLS; x++) { fire[x] = []; for (var y = 0; y < ROWS; y++) fire[x][y] = 0; }
            var pal = [];
            for (var i = 0; i < 64; i++) pal.push([i*4,0,0]);
            for (var i = 0; i < 64; i++) pal.push([255,i*4,0]);
            for (var i = 0; i < 64; i++) pal.push([255,128+i*2,i*4]);
            for (var i = 0; i < 64; i++) pal.push([255,255,128+i*2]);
            function wf(t) {
                for (var x = 0; x < COLS; x++) { for (var y = 0; y < ROWS; y++) fire[x][y] = 0; }
                for (var x = 0; x < COLS; x++) {
                    var h = Math.floor((Math.sin(x/COLS*Math.PI*2+t*0.005)*0.5+0.5)*ROWS*0.7);
                    for (var y = ROWS-1; y >= ROWS-h; y--) fire[x][y] = Math.floor((1-(ROWS-1-y)/h)*200+Math.random()*55);
                }
            }
            function dr() {
                ctx.fillStyle = 'rgba(26,26,46,0.1)'; ctx.fillRect(0,0,W,H);
                for (var x = 0; x < COLS; x++) for (var y = 0; y < ROWS; y++) if (fire[x][y] > 0) {
                    var p = pal[Math.min(255,fire[x][y])];
                    ctx.fillStyle = 'rgb('+p[0]+','+p[1]+','+p[2]+')';
                    ctx.fillRect(x*PX, y*PX, PX-1, PX-1);
                }
            }
            var f = 0;
            function an() { f++; wf(f); dr(); requestAnimationFrame(an); }
            an();
        }
    </script>
    """
    components.html(html, height=80)
