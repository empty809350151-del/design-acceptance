#!/usr/bin/env python3
"""Build a standalone interactive acceptance HTML from a review manifest."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def metric(value: object, percent: bool = True) -> str:
    if percent:
        return f"{float(value):.2f}%"
    return str(int(value))


def issue_svg(issues: list[dict]) -> str:
    chunks = []
    for issue in issues:
        issue_id = int(issue["id"])
        for kind, cls in (("expected_rect", "expected"), ("actual_rect", "problem")):
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
        if actual:
            bx, by = float(actual[0]) + 18, float(actual[1]) + 18
            chunks.append(f'<circle class="badge" cx="{bx}" cy="{by}" r="17"/>')
            chunks.append(f'<text class="badge-text" x="{bx}" y="{by + 1}">{issue_id}</text>')
    return "".join(chunks)


def image_or_placeholder(src: str, image_id: str, alt: str, cls: str = "") -> str:
    if src:
        return f'<img id="{image_id}" class="{cls}" src="{esc(src)}" alt="{esc(alt)}">'
    return f'<div id="{image_id}" class="placeholder {cls}" role="img" aria-label="{esc(alt)}"><span>{esc(alt)}</span></div>'


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
        f'<td class="{"fail" if f.get("flag") else ""}">{float(f["delta"]):+g}</td></tr>'
        for f in fields
    )
    issue_cards = "".join(
        f'<article class="issue" data-issue="{int(i["id"])}" tabindex="0" role="button">'
        f'<h3><span class="num">{int(i["id"])}</span>{esc(i["severity"])} · {esc(i["title"])}</h3>'
        f'<p>{esc(i["design"])}</p></article>'
        for i in issues
    )
    m = page["metrics"]
    attrs = ' hidden' if hidden else ''
    return f'''
    <div class="acceptance-view" data-page="{pid}"{attrs}>
      <header>
        <div class="eyebrow">Design acceptance · {esc(MANIFEST_META["date"])}</div>
        <h1>{esc(page["title"])}<span class="review-title-suffix">Overlay Design Review and Acceptance</span></h1>
        <p class="lead">{esc(page.get("lead", ""))}</p>
        <div class="summary">
          <div class="stat"><strong>{metric(m["overall"])}</strong><span>严格综合分 · {'通过' if float(m['overall']) >= 95 and int(m['critical']) == 0 else '未通过'}</span></div>
          <div class="stat"><strong>{metric(m["pixel"])}</strong><span>Pixel Fidelity</span></div>
          <div class="stat"><strong>{metric(m["structural"])}</strong><span>Multi-scale Structural</span></div>
          <div class="stat"><strong>{metric(m["critical"], False)}</strong><span>P0 关键问题</span></div>
        </div>
      </header>
      <main><section>
        <h2>交互叠图与问题框选</h2>
        <p class="section-note">{esc(page.get("scope_note", ""))}</p>
        <div class="overlay-layout">
          <div class="visual-column">
            <div class="{overlay_class}" style="aspect-ratio:{viewport_width:g}/{viewport_height:g}" data-overlay data-align-offset="{float(page.get('align_offset_percent', 0))}">
              {image_or_placeholder(images.get('design', ''), pid + '-design', page['title'] + '设计稿', 'design-layer')}
              <div class="actual-composite">{image_or_placeholder(images.get('actual', ''), pid + '-actual', page['title'] + '实际截图', 'actual-layer')}</div>
              {image_or_placeholder(images.get('heatmap', ''), pid + '-heat', '差异热区', 'heat-layer') if images.get('heatmap') else ''}
              {image_or_placeholder(images.get('mask', ''), pid + '-mask', '遮罩范围', 'mask-layer') if images.get('mask') else ''}
              <svg class="markup" viewBox="0 0 {viewport_width:g} {viewport_height:g}" aria-label="问题框选层">{issue_svg(issues)}</svg>
            </div>
            <div class="legend"><span><i></i>实际问题区域</span><span><i></i>设计目标位置</span></div>
            <div class="mode-buttons">
              <button data-mode="align">顶部对齐 · 关</button><button data-mode="difference" title="黑色表示两张图像素一致；再次点击可恢复正常叠图">差异模式 · 关</button>
              <button data-mode="heat">差异热区 · 关</button><button data-mode="mask">遮罩范围 · 关</button>
            </div>
            <div class="opacity-control"><label>左侧截图透明度：<span>50%</span></label><input type="range" min="0" max="100" value="50"></div>
          </div>
          <div class="controls">
            <div class="control"><strong>字号不符合要求（{len(flagged)} 项）</strong><p>逐字段按字形左上角锚定；整层位置不影响字号判断。</p><div class="field-grid"></div></div>
            <details class="control"><summary>全部 {len(fields)} 个字段字号检查</summary><div class="table-scroll"><table><thead><tr><th>字段</th><th>设计</th><th>截图估算</th><th>Δ</th></tr></thead><tbody>{rows}</tbody></table></div></details>
            <div class="issues">{issue_cards}</div>
          </div>
        </div>
      </section></main>
      <footer>{esc(page.get("source", ""))}</footer>
      <script type="application/json" class="page-data">{html.escape(json.dumps({'fields': flagged}, ensure_ascii=False))}</script>
    </div>'''


STYLE = r'''
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap');
:root{--bg:#fff;--panel:#fff;--panel-2:#f7f7f5;--text:#000;--muted:#737373;--line:rgba(0,0,0,.10);--red:#d92d20;--green:#22ad01;--cyan:#22ad01;--soft-green:#eff8ec}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;min-width:320px;padding-left:220px;color:var(--text);background:var(--bg);font:17px/1.4 Geist,Arial,"PingFang SC",sans-serif;transition:padding-left .28s ease}.page-shell{margin:0;padding:0}.acceptance-view[hidden]{display:none!important}
.sidebar{position:fixed;inset:0 auto 0 0;z-index:20;width:220px;padding:28px 22px;border-right:1px solid var(--line);background:#fff;transition:width .28s ease,padding .28s ease}.sidebar-content{transition:opacity .18s ease}.sidebar-toggle{position:absolute;top:24px;right:-15px;z-index:2;display:grid;place-items:center;width:30px;height:30px;padding:0;border:1px solid var(--line);border-radius:50%;color:var(--text);background:#fff;box-shadow:0 4px 12px rgba(0,0,0,.08);font-size:18px;line-height:1}.sidebar-toggle:hover{background:var(--panel-2);transform:none}.sidebar-title{margin:0 0 28px;font-size:18px;font-weight:600;letter-spacing:-.02em;white-space:nowrap}.sidebar-meta{display:grid;grid-template-columns:56px 1fr;gap:8px 10px;color:var(--muted);font-size:13px}.sidebar-meta strong{color:var(--text);font-weight:500}.sidebar-rule{height:1px;margin:24px 0;border:0;background:var(--line)}.sidebar-nav{display:grid;gap:4px}.sidebar-nav a{display:block;padding:10px 12px;border-radius:8px;color:#4d4d4d;font-size:14px;text-decoration:none}.sidebar-nav a.active{color:var(--text);background:var(--panel-2);font-weight:500}body.sidebar-collapsed{padding-left:68px}body.sidebar-collapsed .sidebar{width:68px;padding-inline:18px}body.sidebar-collapsed .sidebar-content{visibility:hidden;opacity:0;pointer-events:none}body.sidebar-collapsed .sidebar-toggle{transform:rotate(180deg)}
header,main,footer{width:min(1440px,calc(100% - 40px));margin:0 auto}header{padding:78px 0 56px}.eyebrow{color:var(--muted);font-size:14px;font-weight:500}h1{max-width:780px;margin:22px 0;font-size:clamp(36px,3.25vw,46px);font-weight:500;line-height:1.12;letter-spacing:-.02em}.review-title-suffix{display:block;margin-top:6px;font-size:clamp(18px,2.2vw,30px);line-height:1.2;letter-spacing:-.015em}.lead{max-width:760px;margin:0;color:#262626;font-size:17px;line-height:1.5}.summary{display:grid;grid-template-columns:repeat(4,1fr);margin-top:52px;border-block:1px solid var(--line)}.stat{padding:24px 24px 24px 0}.stat+.stat{padding-left:24px;border-left:1px solid var(--line)}.stat strong{display:block;font-size:32px;font-weight:500;letter-spacing:-.02em}.stat span{color:var(--muted);font-size:14px}
section{margin:10px 0 64px;padding:44px 0;background:var(--panel)}h2{margin:0 0 8px;font-size:30px;font-weight:500;letter-spacing:-.015em}.section-note{margin:0 0 30px;color:var(--muted);line-height:1.5}.overlay-layout{display:grid;grid-template-columns:minmax(240px,380px) minmax(400px,1fr);gap:26px;align-items:start}.overlay-layout>*,.controls{min-width:0}.visual-column{position:sticky;top:18px;min-width:0}.overlay-wrap{position:relative;width:min(100%,32vh,360px);aspect-ratio:750/1624;margin:0 auto;overflow:hidden;border:1px solid var(--line);border-radius:12px;background:#f2f2f0;box-shadow:0 8px 24px rgba(0,0,0,.08)}.overlay-wrap.partial{width:min(100%,54vh,420px)}.overlay-wrap img,.overlay-wrap .placeholder{position:absolute;inset:0;width:100%;height:100%;object-fit:fill}.placeholder{display:grid;place-items:center;color:var(--muted);background:#f2f2f0}.actual-composite{position:absolute;inset:0;opacity:.5;transition:transform .25s ease,opacity .18s ease}.heat-layer,.mask-layer{opacity:0;pointer-events:none;transition:opacity .18s ease}.heat-layer{z-index:3}.mask-layer{z-index:4}.markup{position:absolute;inset:0;z-index:5;width:100%;height:100%;pointer-events:none}.overlay-wrap.show-heat .heat-layer{opacity:.82}.overlay-wrap.show-mask .mask-layer{opacity:.72}.overlay-wrap.difference .actual-composite{opacity:1!important;mix-blend-mode:difference}.problem{fill:rgba(255,93,108,.055);stroke:var(--red);stroke-width:3;stroke-dasharray:10 7;vector-effect:non-scaling-stroke}.expected{fill:none;stroke:var(--cyan);stroke-width:2;stroke-dasharray:8 6;vector-effect:non-scaling-stroke}.badge{fill:var(--red)}.badge-text{fill:#fff;font-size:22px;font-weight:800;text-anchor:middle;dominant-baseline:middle}.problem.is-highlighted{fill:rgba(217,45,32,.16);stroke-width:6;stroke-dasharray:none;animation:anchor-pulse .72s ease-in-out 3}@keyframes anchor-pulse{50%{fill:rgba(217,45,32,.28);stroke-width:9}}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin:12px 0 0;color:var(--muted);font-size:12px}.legend i{display:inline-block;width:18px;margin-right:6px;vertical-align:middle;border-top:2px dashed var(--red)}.legend span:last-child i{border-color:var(--cyan)}.mode-buttons{display:flex;gap:6px;margin-top:14px;overflow-x:auto;padding-bottom:2px}.mode-buttons button{flex:1 1 0;min-width:0;width:auto;padding:9px 6px;border:1px solid var(--line);border-radius:200px;color:var(--text);background:#fff;font:500 12px/1.2 Geist,Arial,sans-serif;white-space:nowrap;cursor:pointer}.mode-buttons button:hover{border-color:#a6a6a1;background:var(--panel-2)}.mode-buttons button.active{border-color:var(--green);color:#187b06;background:var(--soft-green)}.opacity-control{margin-top:14px;padding:14px 0 0;border:0;background:transparent}.opacity-control label{display:block;margin-bottom:10px;color:var(--text);font-weight:500}.opacity-control input{width:100%;height:6px;margin:4px 0;appearance:none;border-radius:999px;background:linear-gradient(to right,var(--green) 0 50%,#e9e9e5 50% 100%);outline:none}.opacity-control input::-webkit-slider-thumb{width:18px;height:18px;appearance:none;border:2px solid var(--green);border-radius:50%;background:#fff;box-shadow:0 2px 6px rgba(0,0,0,.12);cursor:grab}.opacity-control input::-moz-range-thumb{width:16px;height:16px;border:2px solid var(--green);border-radius:50%;background:#fff;box-shadow:0 2px 6px rgba(0,0,0,.12);cursor:grab}
.controls{display:grid;gap:12px}.control{padding:20px;border:1px solid var(--line);border-radius:12px;background:var(--panel-2)}.control>strong{font-size:17px;font-weight:500}.control>p{margin:8px 0 0;color:#4d4d4d;font-size:13px;line-height:1.6}.field-grid,.issues{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}.field-card,.issue{min-width:0;overflow:hidden;border:1px solid var(--line);border-radius:10px;background:#fff;cursor:pointer;transition:border-color .18s ease,background-color .18s ease}.field-card:hover,.field-card:focus-visible,.issue:hover,.issue:focus-visible{border-color:rgba(217,45,32,.42);background:#fffafa;outline:none}.field-card h3{margin:0;padding:14px 16px 0;font-size:15px}.field-card canvas{display:block;width:calc(100% - 24px);height:auto;max-height:150px;margin:12px;border:1px solid var(--line);border-radius:8px;background:#f4f2ec;object-fit:contain}.field-card p{margin:0;padding:0 16px 14px;color:#4d4d4d;font-size:13px;line-height:1.6}.field-card p b{color:var(--text)}.issue{padding:18px 20px}.issue h3{margin:0 0 8px;font-size:16px}.issue p{margin:0;color:#3f3f3f;font-size:14px;line-height:1.6}.num{display:inline-grid;place-items:center;width:24px;height:24px;margin-right:8px;border-radius:50%;color:#fff;background:var(--red);font-size:12px}.fail{color:var(--red)}code{padding:2px 5px;border-radius:4px;color:#18320f;background:var(--soft-green)}details summary{cursor:pointer;color:var(--text);font-weight:500}.table-scroll{max-height:280px;overflow:auto;margin-top:10px}table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:left}th{color:var(--muted);font-weight:500}footer{padding:0 0 64px;color:var(--muted);font-size:13px;text-align:center}
button:focus-visible,input:focus-visible{outline:3px solid rgba(34,173,1,.28);outline-offset:2px}@media(max-width:980px){body,body.sidebar-collapsed{padding-left:0}.sidebar,body.sidebar-collapsed .sidebar{position:static;width:auto;padding:18px 20px;border-right:0;border-bottom:1px solid var(--line)}.sidebar-toggle{top:16px;right:18px}body.sidebar-collapsed .sidebar-content{display:none}.sidebar-title{margin-bottom:12px}.sidebar-meta{display:flex;gap:8px}.sidebar-meta strong{margin-right:14px}.sidebar-rule{margin:14px 0 8px}.sidebar-nav{display:flex;gap:4px;overflow-x:auto}.sidebar-nav a{flex:0 0 auto}.summary{grid-template-columns:1fr}.overlay-layout{grid-template-columns:1fr}.visual-column{position:static}.overlay-wrap{margin:0 auto}}@media(max-width:560px){header,main,footer{width:min(100% - 20px,1440px)}header{padding:46px 4px 34px}h1{font-size:34px}section{padding:22px 0}.mode-buttons button{padding-inline:4px;font-size:11px}.field-grid,.issues{grid-template-columns:1fr}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
'''

SCRIPT = r'''
const pageTitles=__PAGE_TITLES__;function resetViewModes(view){const overlay=view.querySelector('[data-overlay]');if(!overlay)return;overlay.classList.remove('aligned','difference','show-heat','show-mask');const actual=overlay.querySelector('.actual-composite');if(actual){actual.style.transform='';actual.style.opacity='.5'}const slider=view.querySelector('input[type=range]');if(slider){slider.value='50';slider.style.background='linear-gradient(to right,var(--green) 0 50%,#e9e9e5 50% 100%)'}const value=view.querySelector('.opacity-control span');if(value)value.textContent='50%';view.querySelectorAll('[data-mode]').forEach(btn=>{btn.classList.remove('active');const mode=btn.dataset.mode;const label=mode==='align'?'顶部对齐':mode==='heat'?'差异热区':mode==='mask'?'遮罩范围':'差异模式';btn.textContent=`${label} · 关`})}function showPage(id,push=true){const target=document.querySelector(`[data-page="${id}"]`);if(!target)return;document.querySelectorAll('.acceptance-view').forEach(v=>v.hidden=v!==target);document.querySelectorAll('[data-page-target]').forEach(a=>a.classList.toggle('active',a.dataset.pageTarget===id));document.title=pageTitles[id];if(push)history.pushState({},'',`#${id}`);window.scrollTo(0,0);resetViewModes(target);animate(target)}function animate(view){if(!window.gsap||matchMedia('(prefers-reduced-motion: reduce)').matches)return;gsap.fromTo(view.querySelectorAll('.eyebrow,h1,.lead,.stat,section>h2,.overlay-layout'),{autoAlpha:0,y:14},{autoAlpha:1,y:0,stagger:.045,duration:.45,ease:'power2.out'});view.querySelectorAll('.stat strong').forEach(el=>{const raw=el.textContent;const n=parseFloat(raw);const pct=raw.includes('%');const o={n:0};gsap.to(o,{n,duration:1,onUpdate:()=>el.textContent=pct?`${o.n.toFixed(2)}%`:Math.round(o.n),onComplete:()=>el.textContent=raw})})}document.querySelectorAll('[data-page-target]').forEach(a=>a.onclick=e=>{e.preventDefault();showPage(a.dataset.pageTarget)});document.querySelector('.sidebar-toggle').onclick=()=>document.body.classList.toggle('sidebar-collapsed');document.querySelectorAll('[data-overlay]').forEach(overlay=>{const view=overlay.closest('.acceptance-view');const actual=overlay.querySelector('.actual-composite');const slider=view.querySelector('input[type=range]');const value=view.querySelector('.opacity-control span');slider.oninput=()=>{actual.style.opacity=slider.value/100;slider.style.background=`linear-gradient(to right,var(--green) 0 ${slider.value}%,#e9e9e5 ${slider.value}% 100%)`;value.textContent=`${slider.value}%`;renderFields(view)};view.querySelectorAll('[data-mode]').forEach(btn=>btn.onclick=()=>{const mode=btn.dataset.mode;let on;if(mode==='align'){on=overlay.classList.toggle('aligned');actual.style.transform=on?`translateY(${overlay.dataset.alignOffset}%)`:''}else{const cls=mode==='heat'?'show-heat':mode==='mask'?'show-mask':'difference';on=overlay.classList.toggle(cls)}btn.classList.toggle('active',on);btn.textContent=`${mode==='align'?'顶部对齐':mode==='heat'?'差异热区':mode==='mask'?'遮罩范围':'差异模式'} · ${on?'开':'关'}`})});function renderFields(view){const raw=view.querySelector('.page-data').textContent.replaceAll('&quot;','"').replaceAll('&amp;','&').replaceAll('&lt;','<').replaceAll('&gt;','>');const data=JSON.parse(raw);const grid=view.querySelector('.field-grid');grid.innerHTML='';data.fields.forEach(f=>{const card=document.createElement('article');card.className='field-card';card.dataset.issue=f.issue;card.tabIndex=0;card.innerHTML=`<h3>${f.name}</h3><canvas></canvas><p>设计 <b>${f.expected}px</b>，截图估算 <b>${f.estimate}px</b>，差异 <span class="fail">${f.delta>0?'+':''}${f.delta}px</span><br>字高：截图 ${f.actual_ink_height}px / 设计 ${f.design_ink_height}px</p>`;grid.appendChild(card);const canvas=card.querySelector('canvas'),ctx=canvas.getContext('2d'),pad=20,w=Math.min(730,f.crop[0]+40),h=Math.min(170,f.crop[1]+40);canvas.width=w;canvas.height=h;const design=view.querySelector('.design-layer'),actual=view.querySelector('.actual-layer');if(design?.tagName==='IMG'&&actual?.tagName==='IMG'&&design.complete&&actual.complete){ctx.drawImage(design,f.design_anchor[0]-pad,f.design_anchor[1]-pad,w,h,0,0,w,h);ctx.globalAlpha=view.querySelector('input[type=range]').value/100;ctx.drawImage(actual,f.actual_anchor[0]-pad,f.actual_anchor[1]-pad,w,h,0,0,w,h);ctx.globalAlpha=1}else{ctx.fillStyle='#f2f2ef';ctx.fillRect(0,0,w,h);ctx.fillStyle='#777';ctx.fillText('字段锚点叠图预览',20,35)}ctx.strokeStyle='#58d5ff';ctx.beginPath();ctx.moveTo(pad-9,pad);ctx.lineTo(pad+9,pad);ctx.moveTo(pad,pad-9);ctx.lineTo(pad,pad+9);ctx.stroke()})}function focus(source){const view=source.closest('.acceptance-view'),target=view.querySelector(`.problem[data-box="${source.dataset.issue}"]`);if(!target)return;view.querySelectorAll('.problem').forEach(x=>x.classList.remove('is-highlighted'));target.classList.add('is-highlighted');view.querySelector('.overlay-wrap').scrollIntoView({behavior:'smooth',block:'center'});setTimeout(()=>target.classList.remove('is-highlighted'),5000)}document.addEventListener('click',e=>{const s=e.target.closest('[data-issue]');if(s)focus(s)});window.addEventListener('load',()=>document.querySelectorAll('.acceptance-view').forEach(renderFields));window.onpopstate=()=>showPage(location.hash.slice(1)||__FIRST_PAGE__,false);showPage(location.hash.slice(1)||__FIRST_PAGE__,false);
'''


def build(manifest: dict) -> str:
    global MANIFEST_META
    MANIFEST_META = manifest["meta"]
    pages = manifest["pages"]
    if not pages:
        raise ValueError("manifest.pages must not be empty")
    nav = "".join(f'<a href="#{esc(p["id"])}" data-page-target="{esc(p["id"])}">{esc(p["title"])}</a>' for p in pages)
    bodies = "".join(page_html(page, index != 0) for index, page in enumerate(pages))
    titles = {p["id"]: f'{p["title"]} | Overlay Design Review and Acceptance' for p in pages}
    script = SCRIPT.replace("__PAGE_TITLES__", json.dumps(titles, ensure_ascii=False)).replace("__FIRST_PAGE__", json.dumps(pages[0]["id"]))
    meta = manifest["meta"]
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(titles[pages[0]['id']])}</title><style>{STYLE}</style></head><body>
    <aside class="sidebar"><button class="sidebar-toggle" aria-label="收起侧边栏">‹</button><div class="sidebar-content"><h2 class="sidebar-title">{esc(meta.get('title','Design Acceptance'))}</h2><div class="sidebar-meta"><span>设计师</span><strong>{esc(meta.get('designer','—'))}</strong><span>前端</span><strong>{esc(meta.get('frontend','—'))}</strong></div><hr class="sidebar-rule"><nav class="sidebar-nav">{nav}</nav></div></aside>
    <div class="page-shell">{bodies}</div><script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script><script>{script}</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build(manifest), encoding="utf-8")
    print(f"Built {args.output} with {len(manifest['pages'])} page(s)")


if __name__ == "__main__":
    main()
