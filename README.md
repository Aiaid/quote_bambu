# bambu_cc

把 Bambu Lab 打印机的实时状态推到 Quote/0 电纸屏。本地 LAN MQTT + 可选摄像头快照,单容器跑。

**支持机型**:P2S(基线)、P1P / P1S、A1 / A1 mini、X1 / X1C / X1E、H2D / H2DPro。摄像头自动二选一:RTSPS(P2S / X1 / H2)或 port 6000 JPEG TCP(P1 / A1)。其他差异(V2 活跃 tray、H2D 双喷头、AMS HT、字符串型温度、P1 增量推送深合并)都已处理。

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

1. **拿到打印机三件套**：
   - LAN IP（设置 → 网络）
   - 序列号（设置 → 关于）
   - LAN 访问码（设置 → WLAN，8 位数字）
2. **Quote/0 两件套**：API key（`dot_app_...`）+ 设备 SN

> **不需要开 LAN-only / Developer Mode**（P2S/P1/X1/A1）。云模式下 8883/322 已对同一 LAN 开放,只读监听不受 Authorization Control 影响,可与官方 Handy app 并存。**例外**:H2D/H2DPro 必须 LAN-only + Developer Mode(等于失去云端 app)。

## 用法

```bash
git clone https://github.com/Aiaid/quote_bambu.git
cd quote_bambu
cp .env.example .env
# 编辑 .env 填上 5 个值
docker compose up -d
docker compose logs -f
```

默认从 `ghcr.io/aiaid/quote_bambu:latest` 拉预构建多架构镜像(amd64 / arm64,CI 自动 build)。本地改代码调试用 `docker compose --profile dev up bambu_cc_dev`,会 bind-mount 源码 + inline 装依赖。

## 环境变量（.env）

| 变量 | 说明 | 默认 |
|---|---|---|
| `PRINTER_IP` | P2S 局域网 IP | 必填 |
| `PRINTER_SN` | 打印机序列号 | 必填 |
| `PRINTER_ACCESS` | 8 位 LAN 访问码 | 必填 |
| `QUOTE0_API_KEY` | Quote/0 API key | 必填 |
| `QUOTE0_DEVICE_ID` | Quote/0 设备 SN | 必填 |
| `INTERVAL_SECONDS` | 推屏间隔 | `60` |
| `SHOW_CAMERA` | `true` 抓帧作背景 / `false` 纯数据 | `true` |
| `CAMERA_PROTO` | `auto` / `rtsps`(P2S/X1/H2 系列,port 322)/ `jpeg`(P1P/P1S/A1/A1 mini,port 6000 TLS) | `auto` |
| `HMS_IGNORE` | 逗号分隔的 16 位 hex ecode 列表,命中的不切 HMS 全屏(用于 mute 持久性 warning) | 空 |

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

- RTSPS 抓一帧约 5–10 秒;P1/A1 的 JPEG 流通常更快(~1–2 秒)。`INTERVAL_SECONDS` 不要设得比抓帧时间还低
- 1-bit 屏幕颜色不可视,料盘色块只能传达明暗
- 一台容器对一台打印机;多机要复制项目目录改容器名
- HMS 端点偶尔会限速 / 返回 5xx,启动失败不致命,缓存或显示 raw
- H2D 双喷头版面用 `N1 / N2` 两行,会少显示一行 tray;AMS HT 渲染为 `H1 / H2 / ...`
- H2D / H2DPro 必须 LAN-only + Developer Mode 才有本地 MQTT,与官方 Handy app 互斥。其他机型不受此限

## 参考

- [OpenBambuAPI (Doridian)](https://github.com/Doridian/OpenBambuAPI) — MQTT/RTSP/HTTP/TLS 文档
- [PrintSphere (cptkirki)](https://github.com/cptkirki/PrintSphere) — ESP32 固件，V2 协议参考实现
- [bambulabs-api (PyPI)](https://pypi.org/project/bambulabs-api/) — Python 包装
