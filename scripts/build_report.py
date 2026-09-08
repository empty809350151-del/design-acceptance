#!/usr/bin/env python3
"""Build a standalone interactive acceptance HTML from a review manifest."""

from __future__ import annotations

import argparse
import base64
import copy
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


FIGMA_ICON = "data:image/png;base64," + base64.b64encode((Path(__file__).resolve().parents[1] / "assets" / "figma-logo.png").read_bytes()).decode("ascii")

DISCLOSURE_ICON = "data:image/svg+xml;base64," + base64.b64encode((Path(__file__).resolve().parents[1] / "assets" / "disclosure-arrow.svg").read_bytes()).decode("ascii")

COMPARE_ICONS = {mode: "data:image/svg+xml;base64," + base64.b64encode((Path(__file__).resolve().parents[1] / "assets" / f"compare-{mode}.svg").read_bytes()).decode("ascii") for mode in ("overlay", "split")}

TEST_CASE_ICON = "data:image/png;base64," + base64.b64encode((Path(__file__).resolve().parents[1] / "assets" / "test-case-logo.png").read_bytes()).decode("ascii")

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def metric(value: object, percent: bool = True) -> str:
    if percent:
        return f"{float(value):.2f}%"
    return str(int(value))


def issue_svg(issues: list[dict], side: str | None = None) -> str:
    chunks = []
    for issue in issues:
        issue_id = int(issue["id"])
        chunks.append(f'<g class="issue-mark" data-box="{issue_id}">')
        for kind, cls in (("expected_rect", "expected"), ("actual_rect", "problem")):
            if side and kind != side + "_rect":
                continue
            rect = issue.get(kind)
            if not rect:
                continue
            x, y, width, height, *rest = rect
            radius = rest[0] if rest else 0
            chunks.append(
                f'<rect class="{cls}" data-box="{issue_id}" x="{x}" y="{y}" '
                f'width="{width}" height="{height}" rx="{radius}" />'
            )
        actual = issue.get("actual_rect")
        if actual and side != "expected":
            bx, by = float(actual[0]) + 18, float(actual[1]) + 18
            chunks.append(f'<circle class="badge" cx="{bx}" cy="{by}" r="17"/>')
            chunks.append(f'<text class="badge-text" x="{bx}" y="{by + 1}">{issue_id}</text>')
        chunks.append('</g>')
    return "".join(chunks)


def image_or_placeholder(src: str, image_id: str, alt: str, cls: str = "") -> str:
    if src:
        return f'<img id="{image_id}" class="{cls}" src="{esc(src)}" alt="{esc(alt)}">'
    return f'<div id="{image_id}" class="placeholder {cls}" role="img" aria-label="{esc(alt)}"><span>{esc(alt)}</span></div>'


def issue_preview(issue: dict, images: dict, viewport: list) -> str:
    """Show source crops around each finding; missing evidence stays explicit."""
    width, height = map(float, viewport)
    parts = []
    category = issue.get("category")
    annotation = issue.get("annotation", {})
    dimensioned = category == "size" or (category == "spacing" and annotation.get("axis") in ("x", "y"))
    rects = [issue[k] for k in ("actual_rect", "expected_rect") if issue.get(k)]
    max_w = max((float(r[2]) for r in rects), default=width)
    max_h = max((float(r[3]) for r in rects), default=height)
    ruler_pad = max(24, max(max_w, max_h) * .45)
    for kind, rect_key, label in (("actual", "actual_rect", "实际截图"), ("design", "expected_rect", "设计稿")):
        src = images.get(kind)
        overlay_label = ""
        if category == "color":
            value = annotation.get(kind)
            valid = isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value)
            overlay_label = (f'<span class="image-annotation"><i style="background:{value}"></i>{"≈" if kind == "actual" else ""}{value.upper()}</span>' if valid else '<span class="image-annotation">色值待测</span>')
        if category == "spacing":
            value = annotation.get(kind)
            axis = annotation.get("axis")
            valid = axis in ("x", "y") and isinstance(value, (int, float))
            overlay_label = f'<span class="image-annotation">{"水平" if axis == "x" else "垂直"}间距 {"≈" if kind == "actual" else ""}{value:g}px</span>' if valid else '<span class="image-annotation">间距待测</span>'
        rect = issue.get(rect_key)
        if not src:
            content = f'<div class="issue-preview-missing">缺少{label}</div>'
        else:
            x, y, w, h = map(float, rect[:4]) if rect else (0, 0, width, height)
            padding = max(16, min(w, h) * .25)
            left, top = max(0, x - padding), max(0, y - padding)
            crop_width = max(1, min(width, x + w + padding) - left)
            crop_height = max(1, min(height, y + h + padding) - top)
            if dimensioned and rect:
                # Both previews use the same coordinate span, never fit each object separately.
                crop_width, crop_height = max_w + ruler_pad * 2, max_h + ruler_pad * 2
                left, top = x - ruler_pad, y - ruler_pad
            content = (f'<svg class="issue-preview-image" viewBox="{left:g} {top:g} {crop_width:g} {crop_height:g}" role="img" aria-label="{esc(label + "：" + issue["title"])}">'
                       f'<image href="{esc(src)}" width="{width:g}" height="{height:g}" preserveAspectRatio="xMidYMid meet" />')
            if rect:
                content += f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="none" stroke="{"#d92d20" if kind == "actual" else "#0073ff"}" stroke-width="2" vector-effect="non-scaling-stroke" />'
            if dimensioned and rect:
                color = "#d92d20" if kind == "actual" else "#0073ff"
                font_size = max(crop_width, crop_height) / 15
                offset = ruler_pad * .38
                tick = font_size * .3
                prefix = "≈" if kind == "actual" else ""
                horizontal = category == "size" or annotation.get("axis") == "x"
                vertical = category == "size" or annotation.get("axis") == "y"
                content += f'<g class="dimension-rulers" fill="{color}" stroke="{color}" stroke-width="1" font-size="{font_size:g}" font-weight="600">'
                if horizontal:
                    content += (f'<path d="M{x:g},{y-offset:g}h{w:g} M{x:g},{y-offset-tick:g}v{2*tick:g} M{x+w:g},{y-offset-tick:g}v{2*tick:g}" fill="none" vector-effect="non-scaling-stroke" />'
                                f'<text x="{x+w/2:g}" y="{y-offset-font_size*.45:g}" text-anchor="middle" stroke="white" stroke-width="3" paint-order="stroke">{prefix}{w:g}px</text>')
                if vertical:
                    content += (f'<path d="M{x+w+offset:g},{y:g}v{h:g} M{x+w+offset-tick:g},{y:g}h{2*tick:g} M{x+w+offset-tick:g},{y+h:g}h{2*tick:g}" fill="none" vector-effect="non-scaling-stroke" />'
                                f'<text transform="translate({x+w+offset+font_size*.6:g} {y+h/2:g}) rotate(90)" text-anchor="middle" stroke="white" stroke-width="3" paint-order="stroke">{prefix}{h:g}px</text>')
                content += '</g>'
            content += '</svg>'
        parts.append(f'<figure><div class="annotated-image">{content}{overlay_label}</div><figcaption>{label}</figcaption></figure>')
    delta = ""
    if category == "size" and issue.get("actual_rect") and issue.get("expected_rect"):
        aw, ah = map(float, issue["actual_rect"][2:4])
        ew, eh = map(float, issue["expected_rect"][2:4])
        delta = f'<p class="dimension-delta">宽 {aw-ew:+g}px · 高 {ah-eh:+g}px<span>按框选坐标标注 · 左右同倍率</span></p>'
    if category == "spacing" and all(isinstance(annotation.get(k), (int, float)) for k in ("actual", "design")):
        delta = f'<p class="dimension-delta">间距 {annotation["actual"]-annotation["design"]:+g}px<span>标线对应已测量边界 · 左右同倍率</span></p>'
    return '<div class="issue-preview'  + (' has-dimensions' if dimensioned else '') + '">' + ''.join(parts) + '</div>' + delta


def page_html(page: dict, hidden: bool) -> str:
    pid = esc(page["id"])
    viewport = page.get("viewport", [750, 1624])
    if not isinstance(viewport, list) or len(viewport) != 2 or min(viewport) <= 0:
        raise ValueError(f"page {page['id']} viewport must be [positive width, positive height]")
    viewport_width, viewport_height = (float(value) for value in viewport)
    overlay_class = "overlay-wrap partial" if viewport_height / viewport_width < 1.5 else "overlay-wrap"
    images = page.get("images", {})
    fields = page.get("fields", [])
    issues = page.get("issues", [])
    flagged = [field for field in fields if field.get("flag")]
    rows = "".join(
        f'<tr><td>{esc(f["name"])}</td><td>{esc(f["expected"])}</td>'
        f'<td class="{"fail" if f.get("flag") else ""}">{esc(f["estimate"])}</td>'
        f'<td class="{"fail" if f.get("flag") else ""}">{format(float(f["delta"]), "+g") if f.get("delta") is not None else "待检查"}</td></tr>'
        for f in fields
    )
    font_issue_ids = {int(f["issue"]) for f in flagged}
    categories = {"color": "颜色问题", "spacing": "间距问题", "size": "元素尺寸问题", "other": "其他问题"}
    grouped_cards = ""
    for category, label in categories.items():
        members = [i for i in issues if int(i["id"]) not in font_issue_ids and (i.get("category") if i.get("category") in categories else "other") == category]
        if not members and category == "other":
            continue
        cards = "".join(f'<article class="issue" data-issue="{int(i["id"])}" tabindex="0" role="button"><h3><span class="num">{int(i["id"])}</span>【{esc(i["severity"])}】{esc(i["title"])}</h3>{issue_preview(i, images, viewport)}<p>{esc(i["design"])}</p></article>' for i in members)
        grouped_cards += f'<details class="issue-group"><summary>{label}<span class="{"fail" if members else "zero-count"}">（{len(members)}项）</span></summary><div class="issues">{cards}</div></details>'
    design_url = page.get("figma_url", "")
    link_label = f'<img class="figma-logo" src="{FIGMA_ICON}" width="24" height="24" alt="" aria-hidden="true"><span>设计稿地址 &gt;</span>'
    design_link = f'<a class="design-link" href="{esc(design_url)}" target="_blank" rel="noopener noreferrer">{link_label}</a>' if design_url.startswith(("https://", "http://")) else f'<span class="design-link" role="link" aria-disabled="true" title="暂未配置 Figma 地址">{link_label}</span>'
    test_url = page.get("test_case_url") or MANIFEST_META.get("test_case_url", "")
    test_label = f'<img class="figma-logo" src="{TEST_CASE_ICON}" width="24" height="24" alt="" aria-hidden="true"><span>测试用例地址 &gt;</span>'
    test_link = f'<a class="design-link test-case-link" href="{esc(test_url)}" target="_blank" rel="noopener noreferrer">{test_label}</a>' if test_url.startswith(("https://", "http://")) else f'<span class="design-link test-case-link" role="link" aria-disabled="true" title="暂未配置测试用例地址">{test_label}</span>'
    m = page["metrics"]
    identity = " · ".join(str(page[k]) for k in ("platform", "frontend", "case_id", "state") if page.get(k))
    comparison = "".join(
        f'<figure><div class="pair-image" style="aspect-ratio:{viewport_width:g}/{viewport_height:g}">'
        + image_or_placeholder(images.get(kind, ''), pid + '-pair-' + kind, label)
        + f'<svg class="markup" viewBox="0 0 {viewport_width:g} {viewport_height:g}">{issue_svg(issues, side)}</svg></div><figcaption>{label}</figcaption></figure>'
        for kind, side, label in (("actual", "actual", "开发还原截图"), ("design", "expected", "设计稿"))
    )
    attrs = ' hidden' if hidden else ''
    return f'''
    <div class="acceptance-view" data-page="{pid}"{attrs}>
      <header>
        <div class="eyebrow">{esc(MANIFEST_META.get("project", "设计还原验收"))}</div>
        <h1>{esc(page["title"])}</h1>
        <div class="source-links">{design_link}{test_link}</div>
        <div class="summary">
          <div class="stat"><strong>{metric(m["overall"])}</strong><span>严格综合分 · {'通过' if float(m['overall']) >= 95 and int(m['critical']) == 0 else '未通过'}</span></div>
          <div class="stat"><strong>{metric(m["pixel"])}</strong><span>像素保真度</span></div>
          <div class="stat"><strong>{metric(m["structural"])}</strong><span>多尺度结构</span></div>
          <div class="stat"><strong>{metric(m["critical"], False)}</strong><span>P0 关键问题</span></div>
        </div>
      </header>
      <main><section>
        <div class="overlay-layout">
          <div class="visual-column">
            <div class="mode-buttons comparison-switch" data-selected="split"><button data-compare="overlay" aria-pressed="false"><img class="compare-icon" src="{COMPARE_ICONS['overlay']}" width="16" height="16" alt="" aria-hidden="true">叠图对比</button><button data-compare="split" class="active" aria-pressed="true"><img class="compare-icon" src="{COMPARE_ICONS['split']}" width="16" height="16" alt="" aria-hidden="true">分屏对比</button></div>
            <div class="side-by-side">{comparison}</div>
            <div class="overlay-panel" hidden>
            <div class="comparison-stage"><div class="{overlay_class}" style="aspect-ratio:{viewport_width:g}/{viewport_height:g}" data-overlay data-align-offset="{float(page.get('align_offset_percent', 0))}">
              {image_or_placeholder(images.get('design', ''), pid + '-design', page['title'] + '设计稿', 'design-layer')}
              <div class="actual-composite">{image_or_placeholder(images.get('actual', ''), pid + '-actual', page['title'] + '实际截图', 'actual-layer')}</div>
              {image_or_placeholder(images.get('heatmap', ''), pid + '-heat', '差异热区', 'heat-layer') if images.get('heatmap') else ''}
              {image_or_placeholder(images.get('mask', ''), pid + '-mask', '遮罩范围', 'mask-layer') if images.get('mask') else ''}
              <svg class="markup" viewBox="0 0 {viewport_width:g} {viewport_height:g}" aria-label="问题框选层">{issue_svg(issues)}</svg>
            </div>
            </div><div class="legend"><span><i></i>实际问题区域</span><span><i></i>设计目标位置</span></div>
            <div class="mode-buttons">
              <button data-mode="align">顶部对齐 · 关</button><button data-mode="difference" title="黑色表示两张图像素一致；再次点击可恢复正常叠图">差异模式 · 关</button>
              <button data-mode="heat">差异热区 · 关</button><button data-mode="mask">遮罩范围 · 关</button>
            </div>
            <div class="opacity-control"><label>截图透明度：<span>50%</span></label><input type="range" min="0" max="100" value="50"></div>
            </div>
          </div>
          <aside class="controls" aria-label="验收还原问题">
            <div class="issues-heading"><div><h2>验收还原问题</h2><span class="{"fail" if issues else "zero-count"}">共{len(issues)}项</span></div><p>Acceptance Issue</p></div>
            <details class="issue-group" open><summary>字号问题<span class="{"fail" if flagged else "zero-count"}">（{len(flagged)}项）</span></summary><div class="field-grid"></div></details>
            {grouped_cards}
            <details class="control all-fields"><summary>全部 {len(fields)} 个字段字号检查</summary><div class="table-scroll"><table><thead><tr><th>字段</th><th>设计</th><th>截图估算</th><th>Δ</th></tr></thead><tbody>{rows}</tbody></table></div></details>
            <button class="clear-issue" data-clear-issue>清除框选</button>
          </aside>
        </div>
      </section></main>
      <footer><details class="review-context"><summary>验收说明 · {esc(identity)}</summary><p class="lead">{esc(page.get("lead", ""))}</p><p>{esc(page.get("scope_note", ""))}</p></details><p>{esc(page.get("source", ""))}</p></footer>
      <script type="application/json" class="page-data">{html.escape(json.dumps({'fields': [dict(f, severity=next((i['severity'] for i in issues if i['id'] == f['issue']), 'P1')) for f in flagged]}, ensure_ascii=False))}</script>
    </div>'''


STYLE = r'''
:root{--bg:#fff;--panel:#fff;--panel-2:#f8f9fa;--text:#000;--muted:#999;--line:rgba(0,0,0,.1);--red:#d92d20;--green:#0073ff;--cyan:#0073ff;--soft-green:rgba(0,115,255,.06);--sidebar:320px;--inspector:572px;--gutter:48px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-width:320px;padding-left:var(--sidebar);color:var(--text);background:#fff;font:12px/1.4 "PingFang SC",-apple-system,BlinkMacSystemFont,Arial,sans-serif}button,input{font:inherit}button,summary{cursor:pointer}[hidden]{display:none!important}a{color:#0073ff}button:focus-visible,input:focus-visible,a:focus-visible,summary:focus-visible,[role=button]:focus-visible{outline:2px solid #0073ff;outline-offset:3px}
.sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:var(--sidebar);padding:36px 24px;overflow-y:auto;border-right:1px solid var(--line);background:#fff}.sidebar-title{max-width:220px;margin:0;font-size:28px;line-height:1.4;font-weight:500}.sidebar-subtitle{margin:4px 0 28px;color:var(--muted);font-size:10px}.sidebar-project{margin:0 0 12px;font-size:20px;font-weight:500}.sidebar-meta{display:flex;gap:18px;margin-bottom:28px;font-size:12px}.sidebar-meta>div{min-width:0;flex:1}.sidebar-meta>div+div{border-left:1px solid var(--line);padding-left:18px}.sidebar-meta span{display:block;color:var(--muted);margin-bottom:6px}.sidebar-meta strong{display:block;font-weight:400;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.sidebar-toggle{position:fixed;top:12px;left:calc(var(--sidebar) - 28px);width:24px;height:24px;border:0;background:#fff;color:#999;border-radius:4px}.sidebar-nav{display:grid;gap:28px}.nav-group summary{font-size:14px;font-weight:500}.nav-group>div{display:grid;gap:6px;margin-top:12px}.sidebar-nav a{padding:10px 18px;border-radius:8px;font-size:12px;color:#000;text-decoration:none}.sidebar-nav a.active{background:#f5f6f7}.nav-group summary,.issue-group summary{display:flex;align-items:center;list-style:none}.nav-group summary::-webkit-details-marker,.issue-group summary::-webkit-details-marker{display:none}body.sidebar-collapsed{--sidebar:68px}body.sidebar-collapsed .sidebar{padding:36px 10px}body.sidebar-collapsed .sidebar-content{display:none}body.sidebar-collapsed .sidebar-toggle{transform:rotate(180deg)}
.acceptance-view{padding:36px calc(var(--inspector) + var(--gutter)) 24px var(--gutter)}header,main,footer{width:100%;margin:0}header{position:relative}.eyebrow{color:var(--muted);font-size:14px;font-weight:500}h1{margin:12px 0;font-size:28px;line-height:1.4;font-weight:500;overflow-wrap:anywhere}.source-links{display:flex;align-items:center;flex-wrap:wrap;gap:12px 24px}.design-link{display:inline-flex;align-items:center;gap:4px;font-size:14px;text-decoration:none}.figma-logo{display:block;flex:none;width:24px;height:24px;object-fit:contain}.review-context{margin-top:6px;font-size:9px;color:#999}.review-context summary{font-size:9px}.review-context p{color:#666}.summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin-top:18px;padding:18px 0;gap:0}.stat{min-width:0;padding:0 16px}.stat:first-child{padding-left:0}.stat+.stat{border-left:1px solid var(--line)}.stat strong{display:block;font-size:28px;font-weight:500;line-height:1.4}.stat span{display:block;margin-top:6px;font-size:12px;color:#666}section{margin:0;padding:0}h2{font-size:28px;font-weight:500;margin:0}.overlay-layout{display:block}.visual-column{min-width:0}.comparison-switch{display:flex;gap:6px;background:var(--panel-2);padding:6px;border-radius:8px;margin:18px 0 28px;height:44px}.comparison-switch button{flex:1;border:0;border-radius:4px;background:transparent;font-size:14px}.comparison-switch button.active{background:transparent;font-weight:500}.side-by-side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;min-height:500px;background:var(--panel-2);border-radius:8px;overflow:hidden}.side-by-side figure{min-width:0;margin:0;padding:24px 14px;display:flex;flex-direction:column;align-items:center}.side-by-side figure+figure{border-left:1px solid var(--line)}.side-by-side figcaption{font-size:14px;margin:12px 0 0}.pair-image{position:relative;width:100%;max-width:calc(70vh * var(--image-ratio,.462));overflow:hidden;margin:auto}.pair-image>img,.pair-image>.placeholder{display:block;width:100%;height:100%;object-fit:contain}.comparison-stage{min-height:497px;padding:12px 18px;background:var(--panel-2);border-radius:8px;display:grid;place-items:center}.overlay-wrap{position:relative;width:min(100%,calc(70vh * var(--image-ratio,.462)) );overflow:hidden;margin:0 auto}.overlay-wrap.partial{width:min(100%,752px,calc(70vh * var(--image-ratio,1.6)))}.overlay-wrap img,.overlay-wrap .placeholder{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.placeholder{display:grid!important;place-items:center;color:#999;background:#f1f2f3}.placeholder span{font-size:10px;padding:16px}.legend{display:flex;gap:12px;margin:8px 0;font-size:8px;color:#999}.legend i{display:inline-block;width:16px;margin-right:4px;border-top:2px dashed var(--red)}.legend span+span i{border-color:var(--cyan)}.mode-buttons:not(.comparison-switch){display:flex;gap:12px;margin-top:24px}.mode-buttons:not(.comparison-switch) button{flex:1;min-width:0;min-height:40px;padding:8px 4px;border:1px solid transparent;border-radius:4px;background:var(--panel-2);font-size:12px;white-space:nowrap}.mode-buttons:not(.comparison-switch) button.active{color:#0073ff;border-color:#0073ff;background:var(--soft-green)}.opacity-control{margin-top:12px;font-size:10px}.opacity-control label{display:block;margin-bottom:8px}.opacity-control input{width:100%;accent-color:#0073ff}.issue-mark{display:none}.issue-mark.is-selected{display:inline}
.controls{position:fixed;top:0;right:0;bottom:0;width:var(--inspector);overflow-y:auto;padding:36px 24px;border-left:1px solid var(--line);background:#fff;display:flex;flex-direction:column;gap:28px}.issues-heading>div{display:flex;align-items:center;justify-content:space-between;gap:10px}.issues-heading>div>span{font-size:20px;white-space:nowrap}.issues-heading p{color:#999;font-size:10px;margin:4px 0 0}.issue-group summary{font-size:20px;font-weight:500}.field-grid,.issues{display:grid;grid-template-columns:1fr;gap:12px;margin-top:12px}.field-card,.issue{min-width:0;padding:10px 18px;border:1px solid transparent;border-radius:8px;background:var(--panel-2);cursor:pointer}.field-card h3,.issue h3{display:flex;align-items:center;margin:0;font-size:14px;font-weight:500}.field-card canvas{display:block;width:100%;height:auto;max-height:150px;object-fit:contain;margin:8px 0;border:1px solid var(--line);border-radius:8px}.field-card p,.issue p{font-size:10px;line-height:1.7;margin:8px 0 0}.field-card p{font-size:12px}.field-card p b{font-weight:500}.num{display:inline-grid;place-items:center;flex:none;width:16px;height:16px;border-radius:50%;background:var(--red);color:#fff;font-size:8px;margin-right:8px}.fail{color:var(--red)}.field-card:hover,.issue:hover{background:#f1f3f5}.field-card.is-selected,.issue.is-selected{border-color:var(--red)}.all-fields{font-size:10px;color:#666}.table-scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:9px}th,td{padding:8px 4px;border-bottom:1px solid var(--line);text-align:left}.clear-issue{align-self:flex-start;padding:6px 12px;border:1px solid var(--line);border-radius:4px;background:#fff;color:#666;font-size:10px}footer{margin-top:18px;color:#999;font-size:8px}
@media(min-width:1800px){.stat{padding-inline:48px}.stat:first-child{padding-left:0}.stat:last-child{padding-right:0}}
@media(max-width:1700px){:root{--sidebar:240px;--inspector:400px;--gutter:24px}.sidebar{padding:24px 18px}.sidebar-title{font-size:24px}.sidebar-meta{gap:10px;font-size:10px}.sidebar-meta>div+div{padding-left:10px}.controls{padding:24px 18px}.issues-heading h2{font-size:22px}.issues-heading>div>span,.issue-group summary{font-size:16px}.stat strong{font-size:22px}.stat{padding-inline:10px}.stat span{font-size:10px}.acceptance-view{padding-top:24px}h1{font-size:24px}.field-card,.issue{padding:10px 12px}.mode-buttons:not(.comparison-switch){gap:6px}.mode-buttons:not(.comparison-switch) button{font-size:9px}}
@media(max-width:1200px){:root{--sidebar:220px;--inspector:0px;--gutter:18px}.controls{position:static;width:auto;border:0;border-top:1px solid var(--line);margin-top:24px;padding:24px 0}.side-by-side{min-height:420px}.comparison-stage{min-height:420px}.sidebar-title{font-size:22px}}
@media(max-width:720px){body,body.sidebar-collapsed{padding-left:0}.sidebar,body.sidebar-collapsed .sidebar{position:relative;width:100%;padding:18px;border-right:0;border-bottom:1px solid var(--line)}.sidebar-toggle{position:absolute;top:20px;left:auto;right:20px}.sidebar-title{max-width:none;font-size:20px}.sidebar-subtitle{margin-bottom:16px}.sidebar-project{font-size:16px}.sidebar-meta{margin-bottom:16px;max-width:400px}.sidebar-nav{gap:12px}.nav-group>div{display:flex;flex-wrap:wrap}.sidebar-nav a{padding:8px 12px}.acceptance-view{padding:18px 12px}.summary{grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.stat:nth-child(3){padding-left:0;border-left:0}.side-by-side{min-height:280px}.side-by-side figure{padding:16px 6px}.side-by-side figcaption{font-size:10px;margin:10px 0 0}.comparison-stage{min-height:300px;padding:10px}.comparison-switch{margin-bottom:18px}.field-card h3,.issue h3{font-size:12px}h1{font-size:22px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}

.actual-composite{position:absolute;inset:0;opacity:.5;transition:transform .25s ease,opacity .18s ease}.heat-layer,.mask-layer{opacity:0;pointer-events:none;transition:opacity .18s ease}.heat-layer{z-index:3}.mask-layer{z-index:4}.markup{position:absolute;inset:0;z-index:5;width:100%;height:100%;pointer-events:none}.overlay-wrap.show-heat .heat-layer{opacity:.82}.overlay-wrap.show-mask .mask-layer{opacity:.72}.overlay-wrap.difference .actual-composite{opacity:1!important;mix-blend-mode:difference}.problem{fill:rgba(255,93,108,.055);stroke:var(--red);stroke-width:2;stroke-dasharray:10 7;vector-effect:non-scaling-stroke}.expected{fill:none;stroke:var(--cyan);stroke-width:2;stroke-dasharray:8 6;vector-effect:non-scaling-stroke}.badge{fill:var(--red)}.badge-text{fill:#fff;font-size:18px;font-weight:800;text-anchor:middle;dominant-baseline:middle}.problem.is-highlighted{fill:rgba(217,45,32,.16);stroke-width:2;stroke-dasharray:8 6;animation:anchor-pulse .72s ease-in-out 3}@keyframes anchor-pulse{50%{fill:rgba(217,45,32,.28);stroke-width:2}}
'''

STYLE += r'''
body{transition:padding-left 240ms cubic-bezier(.2,.7,.2,1)}
.sidebar{transition:width 240ms cubic-bezier(.2,.7,.2,1),padding 240ms ease}
.sidebar-toggle{transition:left 240ms cubic-bezier(.2,.7,.2,1),transform 240ms ease,color 160ms ease}
.sidebar-nav a,.comparison-switch button,.mode-buttons button,.clear-issue,.field-card,.issue{transition:background-color 160ms ease,color 160ms ease,border-color 160ms ease,box-shadow 160ms ease}
.sidebar-nav a:hover{background:#f5f6f7}.comparison-switch button:not(.active):hover{color:#555}
button:active{filter:brightness(.96)}



.issue-mark.is-selected{animation:mark-reveal 180ms ease-out}.field-card.is-selected,.issue.is-selected{box-shadow:0 0 0 1px rgba(217,45,32,.08)}
@keyframes mark-reveal{from{opacity:0}to{opacity:1}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
'''

STYLE += r'''
.comparison-switch{position:relative;isolation:isolate}
.comparison-switch::before{content:'';position:absolute;top:6px;bottom:6px;left:6px;width:calc((100% - 18px)/2);border-radius:4px;background:#fff;pointer-events:none;transform:translateX(0)}
.comparison-switch[data-selected="split"]::before{transform:translateX(calc(100% + 6px))}
.comparison-switch.animate-selection::before{transition:transform 240ms cubic-bezier(.2,.7,.2,1)}
.comparison-switch button{position:relative;z-index:1;min-width:0;display:flex;align-items:center;justify-content:center;gap:6px}.compare-icon{display:block;flex:none;width:16px;height:16px}
.issues-heading>div>span{font-weight:600}
.design-link{color:#0073ff}.design-link[aria-disabled="true"]{cursor:default}
@media(prefers-reduced-motion:reduce){.comparison-switch::before{transition:none!important}}
'''

STYLE += r'''
.zero-count{color:#13B36B}
.issue-preview{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}
.issue-preview figure{margin:0;min-width:0}.issue-preview-image{display:block;width:100%;height:104px;background:#fff;border-radius:4px}
.issue-preview figcaption{margin-top:4px;font-size:10px;color:#999;text-align:center}
.issue-preview-missing{display:grid;place-items:center;min-height:104px;border-radius:4px;background:#f0f1f2;color:#999;font-size:10px}
.opacity-control input{appearance:none;-webkit-appearance:none;height:6px;border:0;border-radius:999px;box-shadow:none;padding:0}
.opacity-control input::-webkit-slider-runnable-track{height:6px;border:0;border-radius:999px;box-shadow:none;background:transparent}
.opacity-control input::-webkit-slider-thumb{-webkit-appearance:none;width:14px;height:14px;margin-top:-4px;border:0;border-radius:50%;background:#0073ff;box-shadow:none}
.opacity-control input::-moz-range-track{height:6px;border:0;border-radius:999px;background:transparent}
.opacity-control input::-moz-range-thumb{width:14px;height:14px;border:0;border-radius:50%;background:#0073ff;box-shadow:none}
'''

STYLE += r'''
.has-dimensions .issue-preview-image{height:144px}
.dimension-delta{color:var(--red);font-weight:500}.dimension-delta span{display:block;margin-top:2px;color:#999;font-size:10px;font-weight:400}
'''

STYLE += r'''
.annotated-image{position:relative;padding-top:24px;background:#fff;border-radius:4px;overflow:hidden}
.image-annotation{position:absolute;top:4px;left:4px;display:flex;gap:4px;align-items:center;padding:2px 4px;background:rgba(255,255,255,.95);font-size:10px;font-weight:600;color:#333;white-space:nowrap}
.image-annotation i{width:10px;height:10px;border:1px solid rgba(0,0,0,.12);border-radius:2px}
.field-illustration{position:relative;padding-top:24px}.field-illustration canvas{margin-top:0}
.font-annotations{position:absolute;top:4px;left:0;right:0;display:flex;justify-content:space-between;gap:4px;font-size:10px;font-weight:600}.font-annotations span{padding:2px 4px;background:#fff;border-radius:3px;color:#d92d20}.font-annotations span+span{color:#0073ff}
'''

STYLE += r'''
details>summary{display:flex;align-items:center;list-style:none}
details>summary::-webkit-details-marker{display:none}
details>summary::marker{content:''}
details>summary::after{content:'';display:block;flex:0 0 16px;width:16px;height:16px;margin-left:auto;background:url('__DISCLOSURE_ICON__') center/16px 16px no-repeat;transition:transform 220ms ease}
details:not([open])>summary::after,details[data-expanding="false"]>summary::after{transform:rotate(-180deg)}
@media(prefers-reduced-motion:reduce){details>summary::after{transition:none!important}}
'''.replace('__DISCLOSURE_ICON__', DISCLOSURE_ICON)

STYLE += r'''
.sidebar,.controls{scrollbar-width:none;-ms-overflow-style:none}
.sidebar::-webkit-scrollbar,.controls::-webkit-scrollbar{display:none;width:0;height:0}
'''

SCRIPT = r'''
const pageTitles=__PAGE_TITLES__;function resetViewModes(view){setComparison(view,'split');clearIssue(view);const overlay=view.querySelector('[data-overlay]');if(!overlay)return;overlay.classList.remove('aligned','difference','show-heat','show-mask');const actual=overlay.querySelector('.actual-composite');if(actual){actual.style.transform='';actual.style.opacity='.5'}const slider=view.querySelector('input[type=range]');if(slider){slider.value='50';slider.style.background='linear-gradient(to right,var(--green) 0 50%,#e9e9e5 50% 100%)'}const value=view.querySelector('.opacity-control span');if(value)value.textContent='50%';view.querySelectorAll('[data-mode]').forEach(btn=>{btn.classList.remove('active');const mode=btn.dataset.mode;const label=mode==='align'?'顶部对齐':mode==='heat'?'差异热区':mode==='mask'?'遮罩范围':'差异模式';btn.textContent=`${label} · 关`})}function showPage(id,push=true){const target=document.querySelector(`[data-page="${id}"]`);if(!target)return;document.querySelectorAll('.acceptance-view').forEach(v=>v.hidden=v!==target);document.querySelectorAll('[data-page-target]').forEach(a=>a.classList.toggle('active',a.dataset.pageTarget===id));document.title=pageTitles[id];if(push)history.pushState({},'',`#${id}`);window.scrollTo(0,0);resetViewModes(target);animate(target)}function motionAllowed(){return !matchMedia('(prefers-reduced-motion: reduce)').matches}
function reveal(element,distance=6){if(!element||!motionAllowed()||!element.animate)return;element.getAnimations().forEach(a=>a.cancel());element.animate([{opacity:0,transform:`translateY(${distance}px)`},{opacity:1,transform:'translateY(0)'}],{duration:220,easing:'cubic-bezier(.2,.7,.2,1)'})}
function animateMetrics(view){
  view.querySelectorAll('.stat strong').forEach(el=>{
    if(el.metricFrame!==undefined)cancelAnimationFrame(el.metricFrame);
    const target=el.dataset.metricTarget??el.textContent;
    el.dataset.metricTarget=target;
    const value=parseFloat(target),percent=target.endsWith('%');
    const format=n=>percent?`${n.toFixed(2)}%`:String(Math.round(n));
    const finish=()=>{el.textContent=target;delete el.metricFrame};
    if(!Number.isFinite(value)||!motionAllowed()||view.hidden){finish();return}
    el.textContent=format(0);
    const started=performance.now();
    function tick(now){
      if(view.hidden||!motionAllowed()){finish();return}
      const progress=Math.min(1,Math.max(0,(now-started)/1000));
      if(progress===1){finish();return}
      el.textContent=format(value*(1-Math.pow(1-progress,3)));
      el.metricFrame=requestAnimationFrame(tick);
    }
    el.metricFrame=requestAnimationFrame(tick);
  });
}
function animate(view){animateMetrics(view);view.querySelectorAll('.eyebrow,h1,.review-context,.stat,.visual-column,.issues-heading,.issue-group,.all-fields').forEach(el=>reveal(el))}
document.querySelectorAll('[data-page-target]').forEach(a=>a.onclick=e=>{e.preventDefault();showPage(a.dataset.pageTarget)});document.querySelector('.sidebar-toggle').onclick=()=>{const collapsed=document.body.classList.toggle('sidebar-collapsed');const toggle=document.querySelector('.sidebar-toggle');toggle.setAttribute('aria-expanded',String(!collapsed));toggle.setAttribute('aria-label',collapsed?'展开侧边栏':'收起侧边栏');if(!collapsed)reveal(document.querySelector('.sidebar-content'),0)};document.querySelectorAll('[data-overlay]').forEach(overlay=>{const view=overlay.closest('.acceptance-view');const actual=overlay.querySelector('.actual-composite');const slider=view.querySelector('input[type=range]');const value=view.querySelector('.opacity-control span');slider.oninput=()=>{actual.style.opacity=slider.value/100;slider.style.background=`linear-gradient(to right,var(--green) 0 ${slider.value}%,#e9e9e5 ${slider.value}% 100%)`;value.textContent=`${slider.value}%`;renderFields(view)};view.querySelectorAll('[data-mode]').forEach(btn=>btn.onclick=()=>{const mode=btn.dataset.mode;let on;if(mode==='align'){on=overlay.classList.toggle('aligned');actual.style.transform=on?`translateY(${overlay.dataset.alignOffset}%)`:''}else{const cls=mode==='heat'?'show-heat':mode==='mask'?'show-mask':'difference';on=overlay.classList.toggle(cls)}btn.classList.toggle('active',on);btn.textContent=`${mode==='align'?'顶部对齐':mode==='heat'?'差异热区':mode==='mask'?'遮罩范围':'差异模式'} · ${on?'开':'关'}`})});function renderFields(view){const raw=view.querySelector('.page-data').textContent.replaceAll('&quot;','"').replaceAll('&amp;','&').replaceAll('&lt;','<').replaceAll('&gt;','>');const data=JSON.parse(raw);const grid=view.querySelector('.field-grid');grid.innerHTML='';data.fields.forEach(f=>{const card=document.createElement('article');card.className='field-card';card.dataset.issue=f.issue;card.tabIndex=0;card.setAttribute('role','button');card.innerHTML=`<h3><span class="num">${f.issue}</span>【${f.severity}】${f.name}</h3><div class="field-illustration"><canvas></canvas><div class="font-annotations"><span>截图 ≈${f.estimate}px</span><span>设计 ${f.expected}px</span></div></div><p>设计 <b>${f.expected}px</b>，截图估算 <b>${f.estimate}px</b>，差异 <span class="fail">${f.delta>0?'+':''}${f.delta}px</span><br>字高：截图 ${f.actual_ink_height}px / 设计 ${f.design_ink_height}px</p>`;grid.appendChild(card);const canvas=card.querySelector('canvas'),ctx=canvas.getContext('2d'),pad=20,w=Math.min(730,f.crop[0]+40),h=Math.min(170,f.crop[1]+40);canvas.width=w;canvas.height=h;const design=view.querySelector('.design-layer'),actual=view.querySelector('.actual-layer');if(design?.tagName==='IMG'&&actual?.tagName==='IMG'&&design.complete&&actual.complete){ctx.drawImage(design,f.design_anchor[0]-pad,f.design_anchor[1]-pad,w,h,0,0,w,h);ctx.globalAlpha=view.querySelector('input[type=range]').value/100;ctx.drawImage(actual,f.actual_anchor[0]-pad,f.actual_anchor[1]-pad,w,h,0,0,w,h);ctx.globalAlpha=1}else{ctx.fillStyle='#f2f2ef';ctx.fillRect(0,0,w,h);ctx.fillStyle='#777';ctx.fillText('字段锚点叠图预览',20,35)}ctx.strokeStyle='#58d5ff';ctx.beginPath();ctx.moveTo(pad-9,pad);ctx.lineTo(pad+9,pad);ctx.moveTo(pad,pad-9);ctx.lineTo(pad,pad+9);ctx.stroke()})}document.addEventListener('click',e=>{const s=e.target.closest('[data-issue]');if(s)focus(s)});window.addEventListener('load',()=>document.querySelectorAll('.acceptance-view').forEach(renderFields));window.onpopstate=()=>showPage(location.hash.slice(1)||__FIRST_PAGE__,false);showPage(location.hash.slice(1)||__FIRST_PAGE__,false);
'''


SCRIPT += r'''
function clearIssue(view){view.querySelectorAll('.is-selected,.is-highlighted').forEach(el=>el.classList.remove('is-selected','is-highlighted'))}
function setComparison(view,mode,animated=false){const incoming=view.querySelector(mode==='split'?'.side-by-side':'.overlay-panel');const changed=incoming.hidden;const tabs=view.querySelector('.comparison-switch');tabs.classList.toggle('animate-selection',animated&&motionAllowed());tabs.dataset.selected=mode;view.querySelector('.side-by-side').hidden=mode!=='split';view.querySelector('.overlay-panel').hidden=mode!=='overlay';view.querySelectorAll('[data-compare]').forEach(btn=>{const active=btn.dataset.compare===mode;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active))});if(animated&&changed)reveal(incoming)}
function focus(source){const view=source.closest('.acceptance-view');const id=source.dataset.issue;clearIssue(view);const marks=[...view.querySelectorAll('.issue-mark')].filter(el=>el.dataset.box===id);if(!marks.length)return;marks.forEach(el=>{el.classList.add('is-selected');el.querySelector('.problem')?.classList.add('is-highlighted')});source.classList.add('is-selected');}
document.querySelectorAll('.acceptance-view').forEach(view=>{view.querySelectorAll('[data-compare]').forEach(btn=>btn.onclick=()=>setComparison(view,btn.dataset.compare,true));view.querySelector('[data-clear-issue]').onclick=()=>clearIssue(view);view.querySelectorAll('.pair-image,.overlay-wrap').forEach(el=>el.style.setProperty('--image-ratio',String(el.style.aspectRatio.split('/').map(Number).reduce((w,h)=>w/h))));resetViewModes(view)});
document.addEventListener('keydown',event=>{const card=event.target.closest('[data-issue]');if(card&&(event.key==='Enter'||event.key===' ')){event.preventDefault();focus(card)}if(event.key==='Escape'){const view=document.querySelector('.acceptance-view:not([hidden])');if(view)clearIssue(view)}});
'''

SCRIPT += r'''
document.querySelectorAll('details').forEach(detail=>{
  const summary=detail.querySelector(':scope > summary');
  let animation=null,targetOpen=detail.open;
  summary.addEventListener('click',event=>{
    event.preventDefault();
    const start=detail.getBoundingClientRect().height;
    targetOpen=animation?!targetOpen:!detail.open;
    if(animation){animation.onfinish=null;animation.cancel();animation=null}
    if(!motionAllowed()||!detail.animate){detail.open=targetOpen;detail.style.height='';detail.style.overflow='';delete detail.dataset.expanding;return}
    detail.open=true;
    detail.style.height='';
    const end=targetOpen?detail.getBoundingClientRect().height:summary.getBoundingClientRect().height;
    detail.dataset.expanding=String(targetOpen);
    detail.style.overflow='hidden';
    animation=detail.animate([{height:`${start}px`},{height:`${end}px`}],{duration:220,easing:'cubic-bezier(.2,.7,.2,1)'});
    animation.onfinish=()=>{detail.open=targetOpen;detail.style.height='';detail.style.overflow='';delete detail.dataset.expanding;animation=null};
  });
});
'''


def embed_report_images(manifest: dict, asset_dir: Path) -> dict:
    """Package screenshot evidence without retaining local or temporary URLs."""
    manifest = copy.deepcopy(manifest)
    cache = {}
    mime_types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                  '.webp': 'image/webp', '.gif': 'image/gif', '.bmp': 'image/bmp'}
    for page in manifest['pages']:
        for kind, source in page.get('images', {}).items():
            if not source:
                continue
            if source in cache:
                page['images'][kind] = cache[source]
                continue
            if source.startswith('data:'):
                header, separator, payload = source.partition(',')
                if not separator or header not in {f'data:{mime};base64' for mime in mime_types.values()}:
                    raise ValueError(f"{page['id']}/{kind}: use a base64 raster image")
                if not base64.b64decode(payload, validate=True):
                    raise ValueError(f"{page['id']}/{kind}: image is empty")
                embedded = source
            else:
                url = urlsplit(source)
                if url.scheme == 'file' and url.netloc in ('', 'localhost'):
                    path = Path(unquote(url.path))
                elif url.scheme or url.netloc:
                    raise ValueError(f"{page['id']}/{kind}: download remote images first and provide a local path for sharing")
                else:
                    path = Path(source)
                if not path.is_absolute():
                    path = asset_dir / path
                mime = mime_types.get(path.suffix.lower())
                if not mime:
                    raise ValueError(f"{page['id']}/{kind}: unsupported screenshot format: {path.suffix}")
                data = path.read_bytes()
                if not data:
                    raise ValueError(f"{page['id']}/{kind}: image is empty: {path}")
                embedded = f'data:{mime};base64,' + base64.b64encode(data).decode('ascii')
            cache[source] = embedded
            page['images'][kind] = embedded
    return manifest


def build(manifest: dict, asset_dir: Path | None = None) -> str:
    manifest = embed_report_images(manifest, Path(asset_dir) if asset_dir is not None else Path.cwd())
    global MANIFEST_META
    MANIFEST_META = manifest["meta"]
    pages = manifest["pages"]
    if not pages:
        raise ValueError("manifest.pages must not be empty")
    ids = [p['id'] for p in pages]
    if len(ids) != len(set(ids)):
        raise ValueError("page IDs must be unique across platforms and cases")
    groups = {}
    for page in pages:
        groups.setdefault(page.get("nav_group", "验收页面"), []).append(page)
    nav = "".join('<details class="nav-group" open><summary>' + esc(group) + '</summary><div>' + "".join(f'<a href="#{esc(p["id"])}" data-page-target="{esc(p["id"])}">{esc(p.get("platform", ""))} {esc(p.get("nav_label", p["title"]))}</a>' for p in members) + '</div></details>' for group, members in groups.items())
    owners = {"UX": manifest["meta"].get("designer", "—")}
    for page in pages:
        platform = page.get("platform", "前端")
        owners.setdefault("Flutter" if platform == "APP" else platform, page.get("frontend", manifest["meta"].get("frontend", "—")))
    owner_html = "".join(f'<div><span>{esc(role)}</span><strong title="{esc(owner)}">{esc(owner)}</strong></div>' for role, owner in owners.items())
    bodies = "".join(page_html(page, index != 0) for index, page in enumerate(pages))
    titles = {p["id"]: f'{p["title"]} | Overlay Design Review and Acceptance' for p in pages}
    script = SCRIPT.replace("__PAGE_TITLES__", json.dumps(titles, ensure_ascii=False)).replace("__FIRST_PAGE__", json.dumps(pages[0]["id"]))
    meta = manifest["meta"]
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(titles[pages[0]['id']])}</title><style>{STYLE}</style></head><body>
    <aside class="sidebar"><button class="sidebar-toggle" aria-expanded="true" aria-label="收起侧边栏">‹</button><div class="sidebar-content"><h2 class="sidebar-title">Design Acceptance</h2><p class="sidebar-subtitle">Figma Overlay Acceptance</p><h3 class="sidebar-project">{esc(meta.get("project", "设计还原验收"))}</h3><div class="sidebar-meta">{owner_html}</div><nav class="sidebar-nav">{nav}</nav></div></aside>
    <div class="page-shell">{bodies}</div><script>{script}</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, help="Base directory for source images (default: output HTML directory)")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = build(manifest, asset_dir=args.asset_dir or args.output.parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(line.rstrip() for line in report.splitlines()) + "\n", encoding="utf-8")
    print(f"Built shareable single-file HTML: {args.output} ({len(manifest['pages'])} page(s), {args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
