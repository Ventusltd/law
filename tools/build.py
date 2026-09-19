#!/usr/bin/env python3
"""tools/build.py - render index.html from laws.json, and refuse if a law is not whole.

A LAW WITHOUT A KEY IS A CANDIDATE, NOT A LAW. This build checks that every law carries all seven
parts and at least one key, and exits non-zero if any does not, so an unfinished law cannot reach
the page by accident. Keys marked `candidate` are allowed through, because saying "quoted from
memory, do not build on it" is honest, but they are counted and shown on the page.

    python tools/build.py          writes index.html, prints the audit
"""
import io
import json
import sys

REQUIRED = ['id', 'title', 'say', 'mean', 'real', 'eq', 'symbols', 'work', 'wrong', 'keys']

CSS = """
  :root { color-scheme: dark; }
  html { background:#000; }
  body { background:#000; color:#fff; font-family:Courier,monospace; padding:40px; max-width:980px; margin:0 auto; font-size:20px; line-height:1.6; }
  h1 { margin:0 0 6px; }
  a { color:#66ccff; text-decoration:none; } a:hover { text-decoration:underline; }
  header p { color:#aaa; font-size:16px; margin:0 0 10px; }
  .rule { color:#aaa; font-size:15px; border-top:1px solid #333; border-bottom:1px solid #333; padding:14px 0; margin:22px 0 10px; }
  .rule b { color:#00ffff; }
  .rule ol { margin:8px 0 0; padding-left:26px; } .rule li { margin:3px 0; }
  .audit { color:#7a7a7a; font-size:14px; margin:0 0 26px; }
  .audit b { color:#ffbe45; }
  details.area { border-bottom:1px solid #333; }
  details.area > summary { list-style:none; cursor:pointer; padding:14px 0; color:#00ffff; font-weight:bold; letter-spacing:.5px; font-size:24px; }
  details.area > summary::-webkit-details-marker { display:none; }
  details.area > summary::before { content:"[+] "; }
  details.area[open] > summary::before { content:"[-] "; }
  details.area > summary:hover { color:#66ffff; }
  details.nest { margin:0 0 14px 18px; border-bottom:0; }
  details.nest > summary { list-style:none; cursor:pointer; font-size:18px; padding:8px 0; color:#66ccff; font-weight:bold; }
  details.nest > summary::-webkit-details-marker { display:none; }
  details.nest > summary::before { content:"[+] "; color:#00ffff; }
  details.nest[open] > summary::before { content:"[-] "; color:#00ffff; }
  details.nest > summary:hover { color:#9fdcff; }
  .body { margin:0 0 22px 22px; border-left:1px solid #1c1c1c; padding-left:18px; }
  .say { color:#fff; font-size:19px; line-height:1.45; margin:6px 0 4px; }
  .lab { display:block; color:#00ffff; font-size:12px; letter-spacing:.09em; text-transform:uppercase; margin:16px 0 5px; }
  p.t { color:#cfcfcf; font-size:15px; margin:4px 0; }
  p.r { color:#d8c9a8; font-size:15px; margin:4px 0; }
  .eq { background:#0b0b0b; border-left:2px solid #00ffff; padding:11px 13px; margin:7px 0; color:#e8e6e1; font-size:16px; overflow-x:auto; }
  ul.sym { margin:6px 0 0; padding-left:20px; color:#9aa3af; font-size:14px; }
  ul.sym li { margin:3px 0; } ul.sym b { color:#e8e6e1; }
  .work { color:#53ff4c; font-size:15px; margin:4px 0; }
  .wrong { color:#ffbe45; font-size:15px; margin:4px 0; }
  table.keys { width:100%; border-collapse:collapse; font-size:13px; margin:6px 0 0; }
  table.keys td { padding:5px 8px 5px 0; border-bottom:1px solid #161616; vertical-align:top; color:#9aa3af; }
  table.keys td.k { color:#e8e6e1; width:34%; }
  .st { font-weight:bold; text-transform:uppercase; font-size:11px; letter-spacing:.06em; white-space:nowrap; }
  .st-exact,.st-derived { color:#53ff4c; } .st-standard,.st-published { color:#66ccff; }
  .st-measured { color:#00ffff; } .st-candidate { color:#ffbe45; }
  .footer { margin-top:50px; font-size:14px; color:#aaa; line-height:1.5; border-top:1px solid #333; padding-top:18px; }
  .footer a { color:#5a5a5a; }
  @media(max-width:600px){ body{padding:22px;font-size:18px} details.area>summary{font-size:22px} .say{font-size:18px} .eq{font-size:14px} table.keys td.k{width:44%} }
"""


def main():
    d = json.load(io.open('laws.json', encoding='utf-8'))

    # ---- refuse before rendering -----------------------------------------------------------
    problems, counts = [], {}
    for area in d['areas']:
        for law in area['laws']:
            for f in REQUIRED:
                if not law.get(f):
                    problems.append('%s is missing %s' % (law.get('id', '?'), f))
            for k in law.get('keys', []):
                if len(k) != 3 or not all(k):
                    problems.append('%s has a malformed key: %r' % (law['id'], k))
                else:
                    counts[k[2]] = counts.get(k[2], 0) + 1
                    if k[2] not in d['status_meanings']:
                        problems.append('%s uses unknown status %r' % (law['id'], k[2]))
    if problems:
        print('REFUSING TO BUILD. A law that is not whole does not get published.')
        for p in problems:
            print('  ' + p)
        return 1

    nlaws = sum(len(a['laws']) for a in d['areas'])
    nkeys = sum(counts.values())
    ncand = counts.get('candidate', 0)

    out = []
    w = out.append
    w('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">')
    w('<link rel="icon" href="data:,">\n<title>%s</title>' % d['title'])
    w('<meta name="viewport" content="width=device-width, initial-scale=1">')
    w('<style>%s</style>\n</head>\n<body>' % CSS)
    w('<header>\n  <h1>%s</h1>\n  <p>%s</p>\n</header>' % (d['title'], d['lede']))

    w('<div class="rule"><b>How every law is written.</b> In this order, always.<ol>')
    for step in d['format']:
        w('  <li>%s</li>' % step)
    w('</ol>Notation is the last step and never the price of entry.</div>')

    w('<p class="audit">%d laws &middot; %d keys &middot; <b>%d marked candidate</b>, meaning '
      'quoted from memory or illustrative and not yet verified. Do not build on a candidate. '
      'The build refuses to publish a law missing any part or any key.</p>'
      % (nlaws, nkeys, ncand))

    w('<main>')
    for area in d['areas']:
        w('<details class="area"><summary>%s</summary>' % area['name'])
        for law in area['laws']:
            w('  <details class="nest"><summary>%s &middot; %s</summary>' % (law['id'], law['title']))
            w('  <div class="body">')
            w('    <p class="say">%s</p>' % law['say'])
            w('    <span class="lab">What it means</span>')
            w('    <p class="t">%s</p>' % law['mean'])
            w('    <span class="lab">In the real world</span>')
            w('    <p class="r">%s</p>' % law['real'])
            w('    <span class="lab">The maths</span>')
            w('    <div class="eq">%s</div>' % law['eq'])
            w('    <ul class="sym">')
            for s in law['symbols']:
                w('      <li>%s</li>' % s)
            w('    </ul>')
            w('    <span class="lab">A worked number</span>')
            w('    <p class="work">%s</p>' % law['work'])
            w('    <span class="lab">How to show it is wrong</span>')
            w('    <p class="wrong">%s</p>' % law['wrong'])
            w('    <span class="lab">Keys</span>')
            w('    <table class="keys">')
            for what, src, st in law['keys']:
                w('      <tr><td class="k">%s</td><td>%s</td>'
                  '<td class="st st-%s">%s</td></tr>' % (what, src, st, st))
            w('    </table>')
            w('  </div>\n  </details>')
        w('</details>')
    w('</main>')

    w('<div class="footer"><b>Disclaimer:</b> Content provided for general technical documentation '
      'and research purposes only. Laws are stated so that they can be shown to be wrong. Every '
      'number carries a key saying where it came from; a key marked <span class="st st-candidate">'
      'candidate</span> was quoted from memory or is illustrative and must be checked against the '
      'standard before anyone builds anything on it. No warranty is given.<br><br>'
      'Built from <a href="laws.json">laws.json</a> by <a href="tools/build.py">tools/build.py</a>, '
      'which refuses to publish a law that is not whole.<br>'
      'Code under Apache-2.0. Documentation under CC BY 4.0.</div>')
    w('</body>\n</html>')

    io.open('index.html', 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')

    print('built index.html: %d laws, %d keys' % (nlaws, nkeys))
    for st in sorted(counts, key=lambda s: -counts[s]):
        print('  %-10s %3d   %s' % (st, counts[st], d['status_meanings'][st]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
