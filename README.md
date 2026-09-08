# Design Acceptance

这是 `figma-overlay-acceptance` Skill 的独立维护项目，也是 Codex 当前直接加载的安装目录。

工作入口是测试用例文档、Figma 设计稿与本次开发范围。APP/H5 按负责人、用例状态和模块分别验收；截图先等比归一化，再依次按 **字号、颜色、间距、元素尺寸** 四个方面验收，像素与结构分数辅助定位。每个方面记录通过、未通过、待确认或不适用及依据；证据不足不能算通过。合法文案换行单独按布局规则验收。HTML 默认左右对比，可切换叠图，问题框仅在选中时显示。

文档提取与设计节点匹配由执行 Skill 的 agent 使用相应工具完成；Python 脚本本身不读取测试文档、不自动识别设计节点。匹配证据不足或缺少某端截图时保留待确认记录。

## 发送验收报告

生成器默认输出**可直接转发的单文件 HTML**，包含截图、设计图、热区、遮罩、图标及全部样式和交互。通过聊天、邮件或共享盘发送该文件即可，接收人下载后用浏览器打开，无需项目目录或本地服务。

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
