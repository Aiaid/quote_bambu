# Quote Bambu 社区投稿材料

核对日期：2026-10-18。状态：本地待审阅，尚未向 MindReset 创建本次投稿 PR。

## 投稿定位

**Quote Bambu — 在 Quote/0 上查看 Bambu Lab 打印状态。**

投递到 Dot. Community Co-Creation 的 Software → Quote 分类。项目由用户在
自己的主机上运行，使用个人 Quote/0 API key 推送内容；当前采用官方文档 PR
申请收录。以后若提供可直接订阅的托管内容源，再考虑 Content Studio 接入。

## 可直接使用的文件

| 本地文件 | 官方仓库中的目标路径 / 用途 |
|---|---|
| [quote_bambu.mdx](en-US/quote_bambu.mdx) | `en-US/service/co_create/software/quote_bambu.mdx` |
| [quote_bambu.mdx（中文）](zh-Hans-CN/quote_bambu.mdx) | `zh-Hans-CN/service/co_create/software/quote_bambu.mdx` |
| [PR 正文](pr-body.md) | 创建 PR 时粘贴；逐项记录实际检查结果 |
| [原始实拍导出](../media/quote-bambu-live-original.jpg) | README 与介绍页使用的真机照片 |
| [AI 修饰展示图](../media/quote-bambu-live-demo.jpg) | 可选宣传配图，注明 AI 辅助修饰 |

原始实拍导出仅转换格式、应用方向、缩小尺寸并移除元数据，没有 AI 重绘。
它记录拍摄时的版面；当前版本另有日期显示等设置，不以该照片证明所有当前设置
或其他机型均已实测。打印机固件、刷新间隔、供电方式和拍摄时推送模式尚未记录，
不在投稿中推断这些细节。

## 提交步骤

1. 在项目仓库发布原始实拍及 README 更新。两份 MDX 使用
   `raw.githubusercontent.com/Aiaid/quote_bambu/main/docs/media/quote-bambu-live-original.jpg`；
   本地新增图片发布前，这个地址尚不能作为已验证的公开资源。
2. Fork [MindReset/dot_web_docs](https://github.com/MindReset/dot_web_docs)，
   从其默认分支新建 `codex/add-quote-bambu` 分支，使用普通克隆目录。
3. 将中英文 MDX 复制到上表目标路径。
4. 在两种语言的 `service/co_create/software/quote/meta.json` 的 `pages` 数组
   各添加 `"../quote_bambu"`，保留原有条目与顺序。提交时重新核对最新目录结构。
5. 检查 `GithubInfo`、图片链接、frontmatter、导航和中英文功能描述。
   纯文档修改不要求运行测试；若无法查看官网渲染预览，在 PR 中明确说明。
6. 向官方默认分支创建 PR，标题使用：
   `docs: add Quote Bambu printer status dashboard`。
   正文使用本目录模板，日文翻译标为尚未提供。
7. 等待维护者审核；按反馈修改，收录后再更新项目的对外描述。

现有 MIT 许可证和已发布版本不需要为本次文档投稿重新创建。视频不作为本套材料
的提交前置条件。介绍限定于监测功能，不声称控制打印机或所有机型均已通过实测。

## 来源与投稿许可

- [官方贡献说明](https://github.com/MindReset/dot_web_docs/blob/main/CONTRIBUTING.md)
- [官方 PR 模板](https://github.com/MindReset/dot_web_docs/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
- [Quote 软件导航](https://github.com/MindReset/dot_web_docs/blob/main/en-US/service/co_create/software/quote/meta.json)
- [Community Co-Creation](https://dot.mindreset.tech/docs/service/co_create)
- [Content Studio 接入说明](https://dot.mindreset.tech/docs/service/studio/join-content-studio)

官方文档仓库要求投稿材料可按其 CC BY-NC-SA 4.0 许可分享；提交前由作者确认
本次介绍文字与照片可用于该文档。该要求不改变 Quote Bambu 应用代码的 MIT 许可。
无需把发送邮件作为投稿步骤；后续联系使用官方当时公布的联系方式。
