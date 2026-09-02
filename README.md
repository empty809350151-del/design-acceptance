# Figma Overlay Acceptance

这是 `figma-overlay-acceptance` Skill 的独立维护项目，也是 Codex 当前直接加载的安装目录。

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
python3 scripts/build_report.py assets/example-manifest.json --output assets/preview.html
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

修改生成器后，应重新生成 `assets/preview.html` 并运行以上验证。
