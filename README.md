# Quote Bambu

[English](README.en.md) · 简体中文

把 Bambu Lab 打印机的实时状态推到 Quote/0 电纸屏。本地 LAN MQTT +
可选摄像头快照，单容器运行。

> Unofficial community project. Not affiliated with or endorsed by Bambu Lab
> or MindReset/Dot.

**兼容目标**：P2S（主要实测基线）、P1P / P1S、A1 / A1 mini、X1 / X1C /
X1E、H2D / H2DPro。RTSPS（通常为 P2S / X1 / H2）和 port 6000 JPEG
TCP（通常为 P1 / A1）可自动探测。不同机型与固件的 LAN、摄像头和
Developer Mode 行为可能变化；欢迎通过 issue 提交带固件版本的兼容性报告。

![preview](canvas_camera_x3.png)

<sub>Canvas 模式（默认）的摄像头版面。Image 模式见下方对比。</sub>

## 功能

- 本地 MQTT 订阅打印机状态；连接后向本地 request topic 发送一次
  `pushall` 状态刷新请求（不发送打印控制指令）
- RTSPS/JPEG 摄像头抓帧 → cover-crop 16:9 → Floyd-Steinberg dither
  为项目输出所需的 1-bit 图像
- 屏幕版面：
  - 顶条：状态 + 进度 + 时间
  - 左 200×112：摄像头快照
  - 右 96×112：温度（喷头/床/腔体）、AMS 湿度雨滴 + 内温、4 个料盘（颜色块 + 料种 + 剩余量）、ETA、层数
  - 底条：文件名 + 全宽进度条 + %
- HMS 报错时全屏切换到 ALERT 版面，启动时拉 Bambu 官方在线 HMS 表显示英文描述
- ffmpeg 抓帧失败自动降级到纯数据版面

## 两种推送模式（PUSH_MODE）

Quote/0 开放接口有两条通道，本项目都支持，用 `PUSH_MODE` 切换：

| 模式 | 通道 | 怎么画 | 取舍 |
|---|---|---|---|
| `canvas`（默认） | Canvas API `/device/<id>/canvas` | 向 Quote/0 云端提交声明式 `div`/`span` + CSS 静态布局；仅摄像头帧和料盘色块用 `<img>` 承载 PNG | 文字用设备像素字体（`text-pixel-12-zpix` / HMS 用 `text-pixel-16`），更清晰 |
| `image` | Image API `/device/<id>/image` | 用 PIL 把整屏画成一张 1-bit PNG 推上去 | 像素级精确，进度条/雨滴/抖动色块完全可控 |

两种模式渲染的是同一批数据，但**观感不同**：image 用 PIL 的 DejaVu
字体在本地生成图片，canvas 把声明式布局提交给 Quote/0 的渲染服务。
Canvas 版（`quote0_canvas.py`）复刻了 camera / data-only / HMS 三套版面，
并处理了温度列对齐、料种截断、百分比右对齐贴边等细节。

> Canvas 内容块同样需要在 Dot. App 的 Content Studio 里加入设备的 Loop 轮播任务后才会显示（和 Image 块各自独立）。

Image 模式版面（对比顶部的 Canvas 版）：

![image preview](preview_camera_x3.png)

## 准备工作

1. **拿到打印机三件套**：
   - LAN IP（设置 → 网络）
   - 序列号（设置 → 关于）
   - LAN 访问码（设置 → WLAN，8 位数字）
2. **Quote/0 两件套**：API key（`dot_app_...`）+ 设备 SN

> LAN/Developer Mode 要求来自社区协议与有限实测，并非官方稳定接口。
> 某些机型/固件在云模式下即可访问本地 MQTT/摄像头，另一些（尤其 H2
> 系列）可能要求 LAN-only + Developer Mode。请先按打印机当前固件设置
> 测试；固件更新后行为可能改变。

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
| `PRINTER_IP` | 打印机局域网 IP | 必填 |
| `PRINTER_SN` | 打印机序列号 | 必填 |
| `PRINTER_ACCESS` | 8 位 LAN 访问码 | 必填 |
| `PRINTER_LABEL` | 屏幕顶栏显示的机型/名称，如 `X1C`、`A1 mini` | `Bambu` |
| `QUOTE0_API_KEY` | Quote/0 API key | 必填 |
| `QUOTE0_DEVICE_ID` | Quote/0 设备 SN | 必填 |
| `INTERVAL_SECONDS` | 推屏间隔 | `60` |
| `SHOW_CAMERA` | `true` 抓帧作背景 / `false` 纯数据 | `true` |
| `PUSH_MODE` | `canvas` 走 Canvas API 用 div/span/CSS 矢量排版(详见下) / `image` 走 Image API 推整张 PNG | `canvas` |
| `CAMERA_PROTO` | `auto` / `rtsps`(P2S/X1/H2 系列,port 322)/ `jpeg`(P1P/P1S/A1/A1 mini,port 6000 TLS) | `auto` |
| `HMS_IGNORE` | 逗号分隔的 16 位 hex ecode 列表,命中的不切 HMS 全屏(用于 mute 持久性 warning) | 空 |
| `TZ` | 容器时区(IANA 名),影响顶栏时钟和 HMS 时间。slim 镜像默认 UTC | `Asia/Shanghai` (建议) |

启动时会校验必填变量、`PUSH_MODE`、`CAMERA_PROTO` 和正数
`INTERVAL_SECONDS`；配置错误会以退出码 2 停止，而不是带空凭证继续运行。

## 离线预览

不连打印机也能调版面。项目支持 Python 3.9+；建议用虚拟环境安装锁定版本：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.lock
pytest
python3 preview.py
```

输出 4 张 PNG（每张都有 `_x3` 放大版）：
- `preview_camera.png` — 默认摄像头版面
- `preview_printing.png` — 数据 fallback 版面（打印中）
- `preview_idle.png` — 数据 fallback 版面（空闲）
- `preview_hms.png` — HMS 报错版面（含真实英文描述）

改 `fetch_bambu.py` 里 `_render_*` 函数的坐标 → 重跑 `preview.py` 即可所见即所得，不用动容器或打印机。

Canvas 版面同理，跑 `python3 preview_canvas.py`，输出 `canvas_camera.png` / `canvas_dataonly.png` / `canvas_hms.png`（各带 `_x3`）。注意 Canvas 预览是**近似渲染**——本地用 Arial 模拟，真机用像素字体，字宽和截断略有差异，定位看个大概，像素级以真机为准。

## 屏幕版面要素

```
┌─ X1C RUNNING ────────────── 47%  19:57 ─┐
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
- **剩余量**：`tray.remain` 字段；已知且为空时会显示 `0%`

## HMS 错误库

启动时拉 `https://e.bambulab.com/query.php?lang=en&f=hms`，缓存到 `/tmp/bambu_hms.json`。下次断网时回退到缓存；缓存也丢了就只显示 raw ecode（16 位 hex）。

## 安全 / TLS

当前对打印机 MQTT 跳过 TLS 验证（`tls_insecure_set(True)`），存在局域网
中间人风险，只应在可信网络中使用。要严格验证可参考
[OpenBambuAPI 的 ca_cert.pem](https://github.com/Doridian/OpenBambuAPI/blob/main/examples/ca_cert.pem)
配合 SNI（CN=序列号）。

RTSPS 使用的 ffmpeg 构建默认也不验证证书。访问码当前必须出现在 ffmpeg
输入 URL 中：项目会在错误日志中打码，但有权限查看容器进程参数的用户仍
可能在抓帧期间看到访问码。因此只应在可信主机/局域网运行，且不要把打印机
的 MQTT/RTSPS/JPEG 端口暴露到互联网。详见 [SECURITY.md](SECURITY.md)。

## Privacy / Data Flow

- 打印机遥测和可选摄像头画面从局域网读取。
- 为了更新屏幕，渲染后的状态会 POST 到 Quote/0 服务；内容可能包含任务名，
  开启摄像头时还包含抓取的相机图。Canvas 模式同样会把声明式布局与嵌入图像
  提交到 Quote/0 云端，并非完全本地显示。
- 启动时会访问 Bambu HMS 公共端点获取错误说明；失败时使用本地临时缓存或
  仅显示错误码。
- 项目不会主动把打印机 LAN 访问码提交给 Quote/0，但 Quote/0 API key 和
  打印机访问码都会由容器进程读取。请保护 `.env` 和运行主机。

## 已知限制

- RTSPS 抓一帧约 5–10 秒;P1/A1 的 JPEG 流通常更快(~1–2 秒)。`INTERVAL_SECONDS` 不要设得比抓帧时间还低
- 本项目输出为 1-bit，料盘颜色块只能传达明暗
- 一台容器对一台打印机;多机要复制项目目录改容器名
- HMS 端点偶尔会限速 / 返回 5xx,启动失败不致命,缓存或显示 raw
- H2D 双喷头版面用 `N1 / N2` 两行,会少显示一行 tray;AMS HT 渲染为 `H1 / H2 / ...`
- 60 秒刷新适合接电常驻；电池供电时较高刷新频率会缩短续航，可提高
  `INTERVAL_SECONDS`
- LAN/Developer Mode 兼容性依赖机型与固件，社区协议变化可能导致功能失效

## 参与贡献

提交问题或 PR 前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)；安全问题请按
[SECURITY.md](SECURITY.md) 私下报告。版本变化记录在
[CHANGELOG.md](CHANGELOG.md)。

## License

Quote Bambu 自身代码采用 [MIT License](LICENSE)。容器内 FFmpeg 7.1 是启用了
GPLv3 组件的独立可执行程序，仍受 GPL-3.0-or-later 及其静态依赖各自许可证
约束；MIT 不会重新许可这些组件。对应版本、构建来源、源码地址和完整许可证
见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 参考

- [Quote/0 Developer Platform](https://dot.mindreset.tech/docs/service/open) — 官方开放接口
- [Quote/0 Canvas API](https://dot.mindreset.tech/docs/service/open/canvas_api) — Canvas 布局规范
- [Bambu Lab: Third-Party Integration](https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/) — LAN / Developer Mode 官方边界
- [OpenBambuAPI (Doridian)](https://github.com/Doridian/OpenBambuAPI) — MQTT/RTSP/HTTP/TLS 文档
- [PrintSphere (cptkirki)](https://github.com/cptkirki/PrintSphere) — ESP32 固件，V2 协议参考实现
- [bambulabs-api (PyPI)](https://pypi.org/project/bambulabs-api/) — Python 包装
