# bambu_cc

把 Bambu Lab P2S（及兼容 V2 协议机型）的实时状态推到 Quote/0 电纸屏。本地 LAN MQTT + 可选 RTSPS 摄像头快照，单容器跑。

![preview](preview_camera_x3.png)

## 功能

- 本地 MQTT 拉打印机全量状态（不依赖 Bambu 云）
- RTSPS 摄像头抓帧 → cover-crop 16:9 → Floyd-Steinberg dither 到 1-bit
- 屏幕版面：
  - 顶条：状态 + 进度 + 时间
  - 左 200×112：摄像头快照
  - 右 96×112：温度（喷头/床/腔体）、AMS 湿度雨滴 + 内温、4 个料盘（颜色块 + 料种 + 剩余量）、ETA、层数
  - 底条：文件名 + 全宽进度条 + %
- HMS 报错时全屏切换到 ALERT 版面，启动时拉 Bambu 官方在线 HMS 表显示英文描述
- ffmpeg 抓帧失败自动降级到纯数据版面

## 准备工作

1. **打印机屏幕里打开开发者模式**（设置 → 通用 → Developer Mode 或 LAN-only Mode）。Bambu 自 2025 年初的「Authorization Control」固件起，必须显式开启才会让第三方读 8883/322 端口
2. **拿到打印机三件套**：
   - LAN IP（设置 → 网络）
   - 序列号（设置 → 关于）
   - LAN 访问码（设置 → WLAN，8 位数字）
3. **Quote/0 两件套**：API key（`dot_app_...`）+ 设备 SN

## 用法

```bash
cd /Users/anend/Desktop/project/bambu_cc
cp .env.example .env
# 编辑 .env 填上 5 个值
docker compose up -d
docker compose logs -f
```

首次启动 1–2 分钟（容器要装 ffmpeg + dejavu 字体 + pip 装 paho-mqtt/requests/pillow），之后 `restart: always` 重启不会重装。

## 环境变量（.env）

| 变量 | 说明 | 默认 |
|---|---|---|
| `PRINTER_IP` | P2S 局域网 IP | 必填 |
| `PRINTER_SN` | 打印机序列号 | 必填 |
| `PRINTER_ACCESS` | 8 位 LAN 访问码 | 必填 |
| `QUOTE0_API_KEY` | Quote/0 API key | 必填 |
| `QUOTE0_DEVICE_ID` | Quote/0 设备 SN | 必填 |
| `INTERVAL_SECONDS` | 推屏间隔 | `60` |
| `SHOW_CAMERA` | `true` 抓 RTSPS 帧作背景 / `false` 纯数据 | `true` |

## 离线预览

不连打印机也能调版面。装好本地依赖后跑：

```bash
python3 -m pip install --user paho-mqtt requests pillow
python3 preview.py
```

输出 4 张 PNG（每张都有 `_x3` 放大版）：
- `preview_camera.png` — 默认摄像头版面
- `preview_printing.png` — 数据 fallback 版面（打印中）
- `preview_idle.png` — 数据 fallback 版面（空闲）
- `preview_hms.png` — HMS 报错版面（含真实英文描述）

改 `fetch_bambu.py` 里 `_render_*` 函数的坐标 → 重跑 `preview.py` 即可所见即所得，不用动容器或打印机。

## 屏幕版面要素

```
┌─ P2S RUNNING ────────────── 47%  19:57 ─┐
│┌──── 200×112 cam ───┬─ 96×112 right ──┐│
││                     │ N215° B60° C32° ││
││   [16:9 dither]     │ AMS ♦♦♦♦◊ 23°  ││
││                     │ ─────────────   ││
││                     │ □ T1  PLA  80%  ││
││                     │ ■ T2* PETG 65%  ││
││                     │ ▓ T3  PLA-S 30% ││
││                     │ ▫ T4  —         ││
││                     │ ─────────────   ││
││                     │ ETA 2h18m       ││
││                     │ L142/305        ││
│└─────────────────────┴─────────────────┘│
│ benchy_PLA_0.20mm.gcode                 │
│ [████████░░░░░░░░░░░░░░░░░░░░░] 47%     │
└─────────────────────────────────────────┘
```

- **温度行**：`N` 喷头、`B` 热床、`C` 腔体
- **AMS 雨滴**：5 档湿度，1=最干 → 5=最湿，越多实心越湿。AMS-HT 等带 `humidity_raw` 的固件会自动按 0–20%/20–40%/... 转成 5 档
- **料盘色块**：`tray_color` HEX → 亮度（BT.601 加权）→ 7×7 灰度方块经 Floyd-Steinberg dither 出来的 1-bit pattern。白色出空框、黑色实心、中色网点
- **当前进料**：盘号后加 `*`（来自 `ams.tray_now`）
- **剩余量**：`tray.remain` 字段，0 时不显示

## HMS 错误库

启动时拉 `https://e.bambulab.com/query.php?lang=en&f=hms`，缓存到 `/tmp/bambu_hms.json`。下次断网时回退到缓存；缓存也丢了就只显示 raw ecode（16 位 hex）。

## 安全 / TLS

当前对打印机 MQTT 跳过 TLS 验证（`tls_insecure_set(True)`），LAN 内可接受。要严格验证可参考 [OpenBambuAPI 的 ca_cert.pem](https://github.com/Doridian/OpenBambuAPI/blob/main/examples/ca_cert.pem) 配合 SNI（CN=序列号）。

RTSPS 走 ffmpeg 的 `-tls_verify 0`，同理。

## 已知限制

- ffmpeg 抓 RTSPS 一帧约 5–10 秒，影响刷新节奏；`INTERVAL_SECONDS` 不要设得比这低
- 1-bit 屏幕颜色不可视，料盘色块只能传达明暗
- 一台容器对一台打印机；多机要复制项目目录改容器名
- HMS 端点偶尔会限速 / 返回 5xx，启动失败不致命，缓存或显示 raw

## 参考

- [OpenBambuAPI (Doridian)](https://github.com/Doridian/OpenBambuAPI) — MQTT/RTSP/HTTP/TLS 文档
- [PrintSphere (cptkirki)](https://github.com/cptkirki/PrintSphere) — ESP32 固件，V2 协议参考实现
- [bambulabs-api (PyPI)](https://pypi.org/project/bambulabs-api/) — Python 包装
