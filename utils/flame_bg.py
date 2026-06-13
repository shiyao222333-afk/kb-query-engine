"""
像素火焰背景组件 - 用于 Streamlit 应用
用 HTML5 Canvas 实现像素化火焰效果，类似老式播放器的声波显示
"""

import streamlit as st
import streamlit.components.v1 as components


def render_flame_background(
    width: int = 800,
    height: int = 200,
    pixel_size: int = 8,
    key: str = "flame_bg"
):
    """
    渲染像素火焰背景（Canvas 动画，纯代码实现）

    参数:
        width: Canvas 宽度
        height: Canvas 高度
        pixel_size: 像素块大小（越大越像素化）
        key: Streamlit 组件唯一 key
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: #0E1117;
            }}
            canvas {{
                display: block;
                width: 100%;
                height: {height}px;
            }}
        </style>
    </head>
    <body>
        <canvas id="flame-{key}" width="{width}" height="{height}"></canvas>
        <script>
        (() => {{
            const canvas = document.getElementById('flame-{key}');
            const ctx = canvas.getContext('2d');
            const W = canvas.width;
            const H = canvas.height;
            const PX = {pixel_size};  // 像素块大小
            const COLS = Math.floor(W / PX);
            const ROWS = Math.floor(H / PX);

            // 火焰粒子数组 [COLS]
            // 每个元素是一个数组，表示该列的火焰高度（0~ROWS）
            let fire = new Array(COLS).fill(0).map(() => new Array(ROWS).fill(0));

            // 调色板（像素火焰颜色）
            const palette = [];
            // 黑色 -> 深红 -> 橙红 -> 橙黄 -> 黄白
            for (let i = 0; i < 64; i++) {{
                const r = Math.min(255, i * 4);
                const g = Math.min(255, i * 2);
                const b = Math.min(128, i);
                palette.push([r, g, b]);
            }}
            for (let i = 0; i < 64; i++) {{
                const r = 255;
                const g = Math.min(255, 128 + i * 2);
                const b = Math.min(255, i * 4);
                palette.push([r, g, b]);
            }}
            for (let i = 0; i < 128; i++) {{
                const r = 255;
                const g = 255;
                const b = Math.min(255, i * 2);
                palette.push([r, g, b]);
            }}

            // 初始化底部火焰（随机点燃）
            function ignite() {{
                for (let x = 0; x < COLS; x++) {{
                    if (Math.random() > 0.3) {{
                        fire[x][ROWS - 1] = Math.floor(Math.random() * 256);
                    }}
                }}
            }}

            // 火焰传播（Doom 火焰算法简化版）
            function updateFire() {{
                for (let x = 0; x < COLS; x++) {{
                    for (let y = 1; y < ROWS; y++) {{
                        // 从下方获取火焰值，加上随机扩散
                        const below = fire[x][y];
                        if (below > 0) {{
                            // 随机向左或向右扩散
                            const spread = Math.floor(Math.random() * 3) - 1;  // -1, 0, 1
                            const nx = Math.max(0, Math.min(COLS - 1, x + spread));
                            // 火焰向上传播，逐渐减弱
                            const decay = Math.random() > 0.7 ? 1 : 0;
                            fire[nx][y - 1] = Math.max(0, below - decay);
                            fire[x][y] = 0;  // 当前像素火焰已传播
                        }}
                    }}
                }}
                // 底部随机重新点燃
                if (Math.random() > 0.1) {{
                    const x = Math.floor(Math.random() * COLS);
                    fire[x][ROWS - 1] = Math.floor(Math.random() * 256);
                }}
            }}

            // 用像素块绘制火焰
            function drawFire() {{
                ctx.fillStyle = '#0E1117';
                ctx.fillRect(0, 0, W, H);

                for (let x = 0; x < COLS; x++) {{
                    for (let y = 0; y < ROWS; y++) {{
                        const intensity = fire[x][y];
                        if (intensity > 0) {{
                            const [r, g, b] = palette[Math.min(255, intensity)];
                            ctx.fillStyle = `rgb(${{r}}, ${{g}}, ${{b}})`;
                            // 像素块稍微错开，产生动态感
                            const offsetX = (y % 2 === 0) ? 0 : PX * 0.2;
                            ctx.fillRect(
                                x * PX + offsetX,
                                y * PX,
                                PX - 1,
                                PX - 1
                            );
                        }}
                    }}
                }}
            }}

            // 波形火焰模式（类似播放器声波）
            function waveFlame(time) {{
                // 清除火焰
                for (let x = 0; x < COLS; x++) {{
                    for (let y = 0; y < ROWS; y++) {{
                        fire[x][y] = 0;
                    }}
                }}

                // 用正弦波生成火焰高度
                for (let x = 0; x < COLS; x++) {{
                    const normalizedX = x / COLS;
                    // 多个正弦波叠加，产生复杂波形
                    const wave1 = Math.sin(normalizedX * Math.PI * 4 + time * 0.002) * 0.5 + 0.5;
                    const wave2 = Math.sin(normalizedX * Math.PI * 7 + time * 0.003) * 0.3 + 0.5;
                    const wave3 = Math.sin(normalizedX * Math.PI * 2 + time * 0.001) * 0.4 + 0.5;
                    const combined = (wave1 + wave2 + wave3) / 3;

                    // 火焰高度（从底部开始）
                    const flameHeight = Math.floor(combined * ROWS * 0.8);
                    for (let y = ROWS - 1; y >= ROWS - flameHeight; y--) {{
                        // 越往上火焰强度越弱
                        const distFromBottom = ROWS - 1 - y;
                        const intensity = Math.floor(
                            (1 - distFromBottom / flameHeight) * 255 * (0.8 + Math.random() * 0.2)
                        );
                        fire[x][y] = Math.max(0, Math.min(255, intensity));
                    }}
                }}
            }}

            // 动画循环
            let frameCount = 0;
            let mode = 'wave';  // 'wave' 或 'fire'

            function animate() {{
                frameCount++;

                // 每 10 秒切换一次模式
                if (frameCount % 600 === 0) {{
                    mode = mode === 'wave' ? 'fire' : 'wave';
                }}

                if (mode === 'wave') {{
                    waveFlame(frameCount);
                }} else {{
                    ignite();
                    updateFire();
                }}

                drawFire();
                requestAnimationFrame(animate);
            }}

            // 启动动画
            animate();
        }})();
        </script>
    </body>
    </html>
    """

    # 用 streamlit components 渲染 HTML
    components.html(html_code, height=height, width=width, scrolling=False)


def render_flame_css_background():
    """
    用 CSS + JS 实现全屏像素火焰背景（覆盖整个 Streamlit 页面）
    需要在 app.py 最开始调用
    """
    flame_css = """
    <style>
        /* 主容器背景 */
        .main .block-container {
            background: transparent !important;
        }

        /* 侧边栏背景 */
        [data-testid="stSidebar"] {
            background: rgba(14, 17, 23, 0.95) !important;
            backdrop-filter: blur(10px);
        }

        /* 主内容区背景 */
        .stApp {
            background: #0E1117 !important;
        }

        /* 火焰 Canvas 容器（固定在底部） */
        #flame-container {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 200px;
            z-index: -1;
            pointer-events: none;
        }
    </style>

    <!-- 火焰背景 Canvas -->
    <div id="flame-container">
        <canvas id="pixel-flame"></canvas>
    </div>

    <script>
    (() => {
        const canvas = document.getElementById('pixel-flame');
        const ctx = canvas.getContext('2d');

        // 自适应宽度
        function resize() {
            canvas.width = window.innerWidth;
            canvas.height = 200;
        }
        resize();
        window.addEventListener('resize', resize);

        const W = canvas.width;
        const H = canvas.height;
        const PX = 10;  // 像素块大小（越大越像素化）
        const COLS = Math.floor(W / PX);
        const ROWS = Math.floor(H / PX);

        // 火焰数据 [COLS][ROWS]
        let fire = new Array(COLS).fill(0).map(() => new Array(ROWS).fill(0));

        // 调色板（火焰颜色：黑 -> 深红 -> 橙红 -> 橙黄 -> 白）
        const palette = [];
        // 0-63: 黑 -> 红
        for (let i = 0; i < 64; i++) {
            palette.push([i * 4, 0, 0]);
        }
        // 64-127: 红 -> 橙
        for (let i = 0; i < 64; i++) {
            palette.push([255, i * 4, 0]);
        }
        // 128-191: 橙 -> 黄
        for (let i = 0; i < 64; i++) {
            palette.push([255, 128 + i * 2, i * 4]);
        }
        // 192-255: 黄 -> 白
        for (let i = 0; i < 64; i++) {
            palette.push([255, 255, 128 + i * 2]);
        }

        // 随机点燃底部
        function ignite() {
            for (let x = 0; x < COLS; x++) {
                if (Math.random() > 0.4) {
                    fire[x][ROWS - 1] = Math.floor(Math.random() * 256);
                }
            }
        }

        // 火焰传播（Doom 火焰算法）
        function updateFire() {
            for (let x = 0; x < COLS; x++) {
                for (let y = ROWS - 1; y > 0; y--) {
                    const intensity = fire[x][y];
                    if (intensity > 0) {
                        // 向上传播
                        const decay = Math.floor(Math.random() * 3);
                        const newY = y - 1;
                        const newX = Math.max(0, Math.min(COLS - 1, x + Math.floor(Math.random() * 3) - 1));
                        fire[newX][newY] = Math.max(0, intensity - decay);
                        fire[x][y] = 0;
                    }
                }
            }
            // 底部随机补充燃料
            if (Math.random() > 0.05) {
                const x = Math.floor(Math.random() * COLS);
                fire[x][ROWS - 1] = 200 + Math.floor(Math.random() * 56);
            }
        }

        // 波形模式
        function waveFlame(time) {
            for (let x = 0; x < COLS; x++) {
                for (let y = 0; y < ROWS; y++) {
                    fire[x][y] = 0;
                }
            }

            for (let x = 0; x < COLS; x++) {
                const nx = x / COLS;
                const wave = (
                    Math.sin(nx * Math.PI * 3 + time * 0.003) * 0.5 +
                    Math.sin(nx * Math.PI * 7 + time * 0.005) * 0.3 +
                    Math.sin(nx * Math.PI * 1.5 + time * 0.001) * 0.2
                ) * 0.5 + 0.5;

                const h = Math.floor(wave * ROWS * 0.7);
                for (let y = ROWS - 1; y >= ROWS - h; y--) {
                    const dy = ROWS - 1 - y;
                    const intensity = Math.floor((1 - dy / h) * 255 * (0.7 + Math.random() * 0.3));
                    fire[x][y] = Math.min(255, intensity);
                }
            }
        }

        // 绘制
        function draw() {
            ctx.fillStyle = '#0E1117';
            ctx.fillRect(0, 0, W, H);

            for (let x = 0; x < COLS; x++) {
                for (let y = 0; y < ROWS; y++) {
                    const v = fire[x][y];
                    if (v > 0) {
                        const [r, g, b] = palette[Math.min(255, Math.floor(v))];
                        ctx.fillStyle = `rgb(${r},${g},${b})`;
                        // 像素块
                        ctx.fillRect(x * PX, y * PX, PX - 1, PX - 1);
                    }
                }
            }
        }

        // 动画
        let frame = 0;
        let mode = 'wave';

        function loop() {
            frame++;
            if (frame % 900 === 0) mode = mode === 'wave' ? 'fire' : 'wave';

            if (mode === 'wave') {
                waveFlame(frame);
            } else {
                ignite();
                updateFire();
            }

            draw();
            requestAnimationFrame(loop);
        }

        loop();
    })();
    </script>
    """

    st.markdown(flame_css, unsafe_allow_html=True)
