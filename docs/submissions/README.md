# Quote Bambu 社区投稿材料

核对日期：2026-10-18。状态：[MindReset PR #7](https://github.com/MindReset/dot_web_docs/pull/7)
已提交中英文和日文介绍及导航，等待维护者审核。

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
| [quote_bambu.mdx（日文）](ja-JP/quote_bambu.mdx) | `ja-JP/service/co_create/software/quote_bambu.mdx` |
| [PR 正文](pr-body.md) | 已提交正文的本地记录 |
| [原始实拍导出](../media/quote-bambu-live-original.jpg) | README 与介绍页使用的真机照片 |
| [AI 修饰展示图](../media/quote-bambu-live-demo.jpg) | 可选宣传配图，注明 AI 辅助修饰 |

原始实拍导出仅转换格式、应用方向、缩小尺寸并移除元数据，没有 AI 重绘。
它记录拍摄时的版面；当前版本另有日期显示等设置，不以该照片证明所有当前设置
或其他机型均已实测。打印机固件、刷新间隔、供电方式和拍摄时推送模式尚未记录，
不在投稿中推断这些细节。

## 提交记录与后续维护

1. 项目 [PR #18](https://github.com/Aiaid/quote_bambu/pull/18) 已合并，发布了实拍及 README 更新。
   三份 MDX 均引用公开的原始实拍链接；其文件内容与元数据检查过的版本一致。
2. 文档 fork 为 [Aiaid/dot_web_docs](https://github.com/Aiaid/dot_web_docs)，
   投稿分支为 `codex/add-quote-bambu`，使用普通克隆目录准备。
3. 中英文、日文 MDX 均已提交到上表目标路径。
4. 三种语言各自的 `service/co_create/software/quote/meta.json` 中均已添加
   `"../quote_bambu"`，保留其他条目及顺序。
5. 已检查 `GithubInfo`、公开图片链接、frontmatter 结构、导航和翻译一致性。
   未渲染官网页面；本次仅修改文档，未运行 Python 测试。
6. 官方 PR 标题为 `docs: add Quote Bambu printer status dashboard`。
7. 等待维护者审核；后续按反馈同步修改三种语言，收录后再更新项目的对外描述。

现有 MIT 许可证和已发布版本不需要为本次文档投稿重新创建。视频不作为本套材料
的提交前置条件。介绍限定于监测功能，不声称控制打印机或所有机型均已通过实测。

## 来源与投稿许可

- [官方贡献说明](https://github.com/MindReset/dot_web_docs/blob/main/CONTRIBUTING.md)
- [官方 PR 模板](https://github.com/MindReset/dot_web_docs/blob/main/.github/PULL_REQUEST_TEMPLATE.md)
- [Quote 软件导航](https://github.com/MindReset/dot_web_docs/blob/main/en-US/service/co_create/software/quote/meta.json)
- [Community Co-Creation](https://dot.mindreset.tech/docs/service/co_create)
- [Content Studio 接入说明](https://dot.mindreset.tech/docs/service/studio/join-content-studio)

本次介绍文字与照片已由作者授权提交至采用 CC BY-NC-SA 4.0 许可的官方文档仓库。
该文档投稿不改变 Quote Bambu 应用代码的 MIT 许可。
无需把发送邮件作为投稿步骤；后续联系使用官方当时公布的联系方式。
