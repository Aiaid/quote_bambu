# Quote Bambu 加入 Dot. Community Co-Creation：提交草稿

> **状态：仅供作者审核的本地草稿。** 本文没有代表作者联系 MindReset、提交表单、
> 创建 fork、推送分支或创建 Pull Request。执行任何外部操作前，请先确认项目许可、
> 仓库内容、截图脱敏和真机兼容性描述。

## 推荐路径

MindReset 的公开文档仓库明确欢迎通过 fork 和 Pull Request 改进文档，现有社区项目
位于英文和简体中文的 `service/co_create/software` 目录。因此，Quote Bambu 最直接的
申请方式是：

1. 完善 Quote Bambu 自身仓库；
2. 向 `MindReset/dot_web_docs` 同时新增英文和简体中文 MDX；
3. 创建文档 PR，请维护者审核是否收录；
4. 用 `contact@mindreset.tech` 告知项目背景并附上 PR，作为补充沟通。

`https://dot.mindreset.tech/submit` 中的 “Join Content Studio” 是内容源接入申请，
不等同于 Community Co-Creation 文档收录。Quote Bambu 当前是用户自行部署、用个人
API key 推送内容的工具，建议先走文档 PR；只有计划把它运营成供其他用户直接添加的
托管内容源时，再申请 Content Studio。

## 提交前清单

### 必须先处理

- [ ] **选择并加入 `LICENSE`。** 当前仓库无明确许可证，不能把项目宣传为
  “open source”。建议作者根据预期选择常见许可证，并确认所有素材和依赖允许相应
  分发；不确定时先咨询专业人士。
- [ ] 确认仓库公开可访问：`https://github.com/Aiaid/quote_bambu`。
- [ ] 确认默认分支可从全新环境按 README 的 Docker 步骤启动。
- [ ] 确认 CI 测试和镜像构建通过，最好发布一个语义化版本 tag，而不只提供
  `latest`。
- [ ] 检查 Git 历史和当前文件中没有 `.env`、打印机访问码、Dot. API key、设备
  序列号、内网 IP、私人任务名或真实家庭摄像头画面。
- [ ] 由作者确认 README 中的兼容性措辞。没有验证过的机型只能写“兼容目标”，
  不能写“已实测”或“完全兼容”。
- [ ] 在至少一台作者实际拥有的 Quote/0 上记录 Canvas 或 Image 模式的真实显示
  结果、刷新间隔和供电方式；如果尚未完成，就明确标记为开发预览，不拿模拟图冒充
  真机图。
- [ ] 保留非官方声明、兼容性不保证、Privacy / Data Flow 和 TLS / 凭证风险说明。

### 建议补强

- [ ] 在仓库 About 中加入一句英文描述、项目主页（可先指向 README）和 topics：
  `quote-0`, `mindreset`, `bambu-lab`, `e-paper`, `docker`, `mqtt`。
- [ ] 发布首个版本，并提供 amd64 / arm64 镜像的版本化 tag。
- [ ] 准备 10–20 秒短视频，展示“打印机状态变化 → Quote/0 更新”，避免剪辑造成
  “实时零延迟”的误解。
- [ ] 收集机型、固件、摄像头协议、推送模式、主机架构的脱敏兼容性表。
- [ ] 在 issue 模板中提醒用户删除访问码、API key、序列号和摄像头隐私信息。

## 向官方文档仓库提 PR

官方仓库：<https://github.com/MindReset/dot_web_docs>

### 1. Fork、克隆并建分支

在 GitHub 页面点击 **Fork**，然后克隆自己的 fork。以下命令中的
`YOUR_GITHUB_NAME` 替换为自己的账号：

```bash
git clone https://github.com/YOUR_GITHUB_NAME/dot_web_docs.git
cd dot_web_docs
git remote add upstream https://github.com/MindReset/dot_web_docs.git
git fetch upstream
git checkout -b docs/add-quote-bambu upstream/main
```

### 2. 同时新增英文和中文 MDX

建议文件名保持两种语言一致：

```text
en-US/service/co_create/software/quote_bambu.mdx
zh-Hans-CN/service/co_create/software/quote_bambu.mdx
```

当前软件目录通过目录内容自动生成导航，通常不需要手工修改
`software/index.mdx` 或 `meta.json`。提交前仍应对照官方仓库最新结构；如果维护者
已经调整导航方式，以最新仓库为准。

英文 MDX 草稿：

```mdx
---
title: Quote Bambu
description: Display local Bambu Lab printer status and optional camera snapshots on Quote/0 through the Canvas or Image API.
new: true
---

<GithubInfo owner="Aiaid" repo="quote_bambu" />

Quote Bambu is a self-hosted bridge that reads Bambu Lab printer telemetry over local-LAN MQTT and sends a compact status dashboard to a Quote/0 e-paper display. It can use the Quote/0 Canvas API for device-font layouts or the Image API for a locally rendered 1-bit frame, with an optional dithered camera snapshot.

### Features

- **Printer dashboard**: Shows state, progress, temperatures, AMS information, filament trays, ETA, layers, and job name
- **Two rendering paths**: Supports both Quote/0 Canvas API and Image API output
- **Camera fallback**: Uses RTSPS or JPEG camera input when available and falls back to a data-only layout
- **HMS alerts**: Displays printer health codes with cached English descriptions when available
- **Self-hosted deployment**: Runs as a Docker container on the user's own trusted LAN

<Callout type="warn" title="Unofficial integration and privacy">
  This is an unofficial community project and is not affiliated with Bambu Lab
  or MindReset. Model and firmware compatibility is not guaranteed. Printer
  telemetry, job names, and optional camera frames are sent to the Quote/0
  service for display. Users should review the project's security and privacy
  notes, protect both access credentials, and run it only on a trusted network.
</Callout>
```

简体中文 MDX 草稿：

```mdx
---
title: Quote Bambu
description: 通过 Canvas API 或 Image API，在 Quote/0 上显示 Bambu Lab 打印机的局域网状态和可选摄像头快照。
new: true
---

<GithubInfo owner="Aiaid" repo="quote_bambu" />

Quote Bambu 是一个可自行部署的桥接工具：它通过局域网 MQTT 读取 Bambu Lab 打印机遥测，并把紧凑的状态面板发送到 Quote/0 电子墨水屏。项目既可使用 Quote/0 Canvas API 生成设备字体版面，也可通过 Image API 推送本地渲染的 1-bit 图片，并支持可选的抖动摄像头快照。

### 功能特性

- **打印状态面板**：显示状态、进度、温度、AMS、料盘、ETA、层数和任务名
- **两种渲染通道**：支持 Quote/0 Canvas API 与 Image API
- **摄像头降级**：可读取 RTSPS 或 JPEG 摄像头，失败时回退到纯数据版面
- **HMS 提醒**：显示打印机健康代码，并在可用时使用缓存的英文说明
- **自行部署**：以 Docker 容器运行在用户自己的可信局域网内

<Callout type="warn" title="非官方集成与隐私提醒">
  本项目为非官方社区项目，与 Bambu Lab 或 MindReset 无隶属或背书关系，且不保证所有
  机型和固件兼容。为了在屏幕上显示，打印机遥测、任务名和可选摄像头画面会发送到
  Quote/0 服务。用户应先阅读项目的安全与隐私说明，保护两类访问凭证，并仅在可信网络
  中运行。
</Callout>
```

这两段只描述当前仓库可核对的功能，没有声称所有机型均经过真机测试。选择许可证后，
如希望使用 “open-source”，再统一更新项目 README、MDX 和 PR 文案。

### 3. 本地检查、提交并推送

先阅读官方仓库最新 README 和贡献说明，再使用仓库实际提供的检查命令。至少人工检查：

- frontmatter 能正常解析；
- `<GithubInfo>` 的 owner/repo 正确；
- 英文和中文文件路径、功能点与风险提示一致；
- 没有密钥、序列号、内网地址或隐私图片；
- 链接可访问，项目 README 与 MDX 不互相矛盾。

确认后再执行：

```bash
git status
git diff --check
git add en-US/service/co_create/software/quote_bambu.mdx \
        zh-Hans-CN/service/co_create/software/quote_bambu.mdx
git commit -m "docs: add Quote Bambu community integration"
git push -u origin docs/add-quote-bambu
```

然后在 GitHub 上将该分支向 `MindReset/dot_web_docs:main` 创建 PR。不要顺带修改
无关文档；如果维护者要求日文版，再单独补充准确翻译。

## PR 模板

建议标题：

```text
docs: add Quote Bambu community integration
```

建议正文：

```markdown
## Summary

Adds English and Simplified Chinese Community Co-Creation pages for Quote Bambu,
a self-hosted bridge that displays local Bambu Lab printer status on Quote/0
through the Canvas or Image API.

## Included

- matching EN and ZH-CN MDX pages
- concise feature and deployment overview
- unofficial-project, compatibility, privacy, and trusted-LAN warnings

## Project

- Repository: https://github.com/Aiaid/quote_bambu
- Deployment: Docker, amd64 / arm64
- Quote/0 APIs: Canvas API and Image API

## Verification

- [ ] Both MDX files follow the current co-create/software structure
- [ ] Links and GitHub owner/repository are correct
- [ ] No credentials, serial numbers, private job names, or camera images are included
- [ ] Compatibility claims are limited to documented targets and do not claim universal hardware testing

This is an unofficial community integration and is not affiliated with or
endorsed by Bambu Lab or MindReset. Feedback on wording and placement is welcome.
```

## 联系 MindReset 的邮件模板

收件人：`contact@mindreset.tech`

### 中文

主题：

```text
Community Co-Creation 投稿：Quote Bambu（Bambu Lab 打印状态上屏）
```

正文：

```text
MindReset 团队你好：

我开发了 Quote Bambu，一个可自行部署的社区工具。它通过局域网 MQTT 读取
Bambu Lab 打印机状态，并通过 Quote/0 Canvas API 或 Image API 显示状态、进度、
温度、AMS、料盘、ETA、层数和可选摄像头快照。

项目仓库：
https://github.com/Aiaid/quote_bambu

Community Co-Creation 文档 PR：
[创建 PR 后填写链接]

项目已在 README 中说明：这是非官方集成，不保证所有机型/固件兼容；打印任务名和
可选摄像头画面会为显示目的发送到 Quote/0 服务；用户应保护访问凭证并仅在可信局域网
运行。

想请你们审核它是否适合收录到 Community Co-Creation 的 Software 分类。如需要调整
文案、截图格式、许可证或测试说明，我愿意配合。

谢谢！
[姓名或 GitHub 用户名]
```

### English

Subject:

```text
Community Co-Creation submission: Quote Bambu printer dashboard
```

Body:

```text
Hello MindReset team,

I built Quote Bambu, a self-hosted community tool that reads Bambu Lab printer
status over local-LAN MQTT and displays status, progress, temperatures, AMS,
filament trays, ETA, layers, and an optional camera snapshot on Quote/0 through
the Canvas or Image API.

Project repository:
https://github.com/Aiaid/quote_bambu

Community Co-Creation documentation PR:
[add the PR URL after it has been created]

The project documentation makes clear that this is an unofficial integration;
model and firmware compatibility is not guaranteed; job names and optional
camera frames are sent to the Quote/0 service for display; and users must
protect both credentials and run the service only on a trusted LAN.

Could you please review whether it is suitable for the Software section of
Community Co-Creation? I would be happy to adjust the wording, media, licensing,
or verification details based on your guidance.

Thank you,
[name or GitHub username]
```

## 截图与视频清单

对外使用前，应准备以下素材；所有素材都要先脱敏：

1. **Quote/0 真机正面照**：显示正常打印状态，画面可读，避免拍到家庭环境和人脸。
2. **Canvas 模式真机照**：说明机型、固件、刷新间隔和供电方式。
3. **Image 模式真机照**：仅在确实完成真机验证后使用。
4. **纯数据降级图**：关闭摄像头或摄像头不可用时的真实/明确标注的预览。
5. **HMS 页面**：优先用合成测试数据；不要为截图人为制造设备故障。
6. **10–20 秒演示视频**：打印机状态变化、服务日志中的一次成功推送、Quote/0
   更新结果。剪辑和字幕要标明实际刷新间隔。
7. **架构图**：`Bambu printer (LAN MQTT/camera) → Quote Bambu container →
   Quote/0 cloud API → Quote/0`，明确相机和任务名会离开局域网。
8. **Docker 启动图**：只能展示脱敏后的成功日志，不能出现 `.env`、完整 URL、
   access code、API key、设备序列号、内网 IP 或私人任务名。

项目现有 `canvas_camera_x3.png` 和 `preview_camera_x3.png` 是开发预览。若用在投稿
或宣传中，必须标为 preview/mockup，不能写成真机实拍。

## 官方 URL

### MindReset / Dot.

- Quote/0 产品文档：<https://dot.mindreset.tech/docs/quote_0>
- Community Co-Creation：<https://dot.mindreset.tech/docs/service/co_create>
- Software 共创列表：<https://dot.mindreset.tech/docs/service/co_create/software>
- Developer Platform：<https://dot.mindreset.tech/docs/service/open>
- Image API：<https://dot.mindreset.tech/docs/service/open/image_api>
- Canvas API：<https://dot.mindreset.tech/docs/service/open/canvas_api>
- 内容创意 / Content Studio 申请：<https://dot.mindreset.tech/submit>
- 联系方式：<https://dot.mindreset.tech/docs/contact>
- 官方文档仓库：<https://github.com/MindReset/dot_web_docs>

### Bambu Lab

- Bambu Lab 官网：<https://bambulab.com/>
- 官方 Third-Party Integration / Developer Mode 说明：
  <https://blog.bambulab.com/updates-and-third-party-integration-with-bambu-connect/>

Bambu Lab 的文章明确说明 Developer Mode 面向高级用户，相关通信协议并非正式受支持，
且用户需要自行承担局域网安全责任。对 Bambu 社区推广时应保留这一边界，不要暗示
Bambu 官方支持本项目或保证未来固件兼容。

## 建议执行顺序

1. 选定许可证并发布 `LICENSE`；
2. 在作者真实设备上完成最小验证并记录环境；
3. 发布首个版本 tag 和版本化容器镜像；
4. 完成脱敏真机图与短视频；
5. fork 官方文档仓库，新增 EN + ZH-CN MDX；
6. 创建 PR；
7. 将 PR 链接放入邮件，发给 `contact@mindreset.tech`；
8. 根据维护者意见修改，不在合并前宣称“已加入官方 Community Co-Creation”。

再次强调：本文只是执行草稿，当前没有进行任何外部提交或联系。
