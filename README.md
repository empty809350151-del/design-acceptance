# Design Acceptance

![Design Acceptance — Figma Design Review](assets/design-acceptance-banner.png)

Design Acceptance 是一个用于 APP/H5 设计还原验收的 Skill，根据测试用例截图与 Figma 设计稿生成可交互的验收报告。

GitHub 仓库名和 Skill 标识统一为 `design-acceptance`，在对话中使用 `$design-acceptance` 调用。

工作入口是测试用例文档、Figma 设计稿与本次开发范围。APP/H5 按负责人、用例状态和模块分别验收；截图先等比归一化，再依次按 **字号、颜色、间距、元素尺寸** 四个方面验收，像素与结构分数辅助定位。每个方面记录通过、未通过、待确认或不适用及依据；证据不足不能算通过。合法文案换行单独按布局规则验收。HTML 默认左右对比，可切换叠图，问题框仅在选中时显示。

文档提取与设计节点匹配由执行 Skill 的 agent 使用相应工具完成；Python 脚本本身不读取测试文档、不自动识别设计节点。匹配证据不足或缺少某端截图时保留待确认记录。

## 安装

将公开仓库克隆到 Codex 的 Skill 目录：

```bash
git clone https://github.com/empty809350151-del/design-acceptance.git ~/.codex/skills/design-acceptance
```

如果已经安装，在没有未提交改动时更新：

```bash
git -C ~/.codex/skills/design-acceptance pull --ff-only
```

执行验收的 agent 需要能够读取测试用例文档及其原始图片，并访问对应 Figma 文件。请先在所用工具中完成相关授权。

## 使用说明

### 1. 准备验收资料

- 测试用例文档或本地文件，包含原始截图、用例编号、平台和页面状态。
- Figma 设计链接，尽量定位到对应页面或组件节点。
- 本次开发范围，包括需要验收的页面、模块及相关布局关系。
- 需求名称、设计负责人、APP/H5 开发负责人。

### 2. 在 Codex 中调用

在对话中输入以下内容，并替换其中的占位信息：

```text
使用 $design-acceptance 进行设计验收。

需求名称：<本次验收的需求名称>
测试用例：<文档链接或本地文件路径>
Figma：<对应设计节点链接>
开发范围：<需要验收的页面、模块及相关布局关系>
验收平台：APP、H5
设计负责人：<姓名>
APP 开发负责人：<姓名>
H5 开发负责人：<姓名>

```

Skill 会按平台、用例状态和变更模块拆分验收单元，匹配设计节点、等比归一化截图，并记录具体元素的测量依据。缺失截图或设计匹配不明确时，会保留待确认项。

### 3. 查看与分享结果

用浏览器打开输出的 HTML，在侧边栏切换 APP/H5 或不同页面；默认左右对比，可切换叠图并调整透明度。点击问题卡片查看对应位置和证据。

生成器默认输出**可直接转发的单文件 HTML**，包含截图、设计图、热区、遮罩、图标及全部样式和交互。通过聊天、邮件或共享盘发送该文件即可，接收人下载后用浏览器打开，无需项目目录或本地服务。

仓库自带的 `assets/example-manifest.json` 和 `assets/preview.html` 是演示数据与占位预览，不是真实验收案例。实际报告及原始证据保存在各任务的输出目录中。

## 手动运行脚本

以下命令在仓库根目录执行。报告生成器仅使用 Python 标准库；图片分析另需 Pillow 和 NumPy，可在虚拟环境中安装：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install Pillow numpy
```

虚拟环境仅用于本地运行，不要提交到仓库。

生成示例报告（截图为占位内容）：

```bash
python3 scripts/build_report.py assets/example-manifest.json --output /tmp/design-acceptance-preview.html
```

分析真实截图前，按 [分析配置说明](references/analysis-config.md) 编写 `analysis-config.json`，指定源图、视口、缩放依据和验收区域，然后运行：

```bash
python3 scripts/analyze_overlay.py analysis-config.json
```

脚本输出归一化截图、设计图、差异热区、遮罩及指标 JSON。图片分析配置中的相对路径按当前工作目录解析。指标不能直接代替人工或 agent 的逐项验收结论，也不是报告清单；按 [清单格式](references/manifest-schema.md) 将图片、测量依据与问题组织到 `report-manifest.json`，再生成报告：


```bash
python3 scripts/build_report.py report-manifest.json --asset-dir ./images --output ./outputs/验收报告.html
```

不指定 `--asset-dir` 时，源图片相对输出目录解析。图片缺失会报错；远程临时图片先下载再生成。单文件会比原图片总量更大，适合附件或共享盘分发。若需要在线访问链接，应部署到指定的静态托管空间；本地文件路径不等于线上分享地址。

## 维护入口

- `SKILL.md`：触发条件、工作流与输出约束
- `scripts/analyze_overlay.py`：叠图指标与差异分析
- `scripts/build_report.py`：交互式验收报告生成器
- `scripts/test_build_report.py`：报告样式与交互回归检查
- `references/`：验收标准、配置与清单规范
- `assets/preview.html`：使用示例清单生成的预览

## 验证

```bash
python3 scripts/test_build_report.py
python3 scripts/test_metric_animation.py
python3 scripts/test_analyze_overlay.py
python3 scripts/build_report.py assets/example-manifest.json --output assets/preview.html
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

修改生成器后，应重新生成 `assets/preview.html` 并运行以上验证。

## 固定 HTML 输出

当前预览样式与交互动效已固化为 Skill 的默认输出。完整规范见 [references/html-output.md](references/html-output.md)，包括字号与间距、图片下方图注、Figma 图标链接、加粗总数、Tab 滑动底板、折叠与切页动效。

生成器 `scripts/build_report.py` 是唯一模板来源。后续验收通过清单填充内容，不另写或后处理页面样式；`assets/preview.html` 是可重复生成的参考输出。图标 `assets/figma-logo.png` 随 Skill 分发并内嵌到报告，样式与动效不依赖联网资源。

浏览器验证（需要 Playwright 与 Chromium）：

```bash
python3 scripts/test_report_browser.py
python3 scripts/test_report_motion.py
python3 scripts/test_issue_presentation.py
```

覆盖正常／减少动画、快速反向折叠、APP/H5 切换及桌面／窄屏。禁止给固定问题栏的祖先添加 transform 动画，以免改变定位基准。
