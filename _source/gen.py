"""Generate the folder-style SVG assets for the GitHub profile README (dark + light)."""
import base64, io, os, sys
from fontTools.ttLib import TTFont
from fontTools import subset

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
FD = '/usr/share/fonts/opentype/inter/'
FONTS = {'m': 'InterDisplay-Medium.otf', 'mi': 'InterDisplay-MediumItalic.otf', 'sb': 'InterDisplay-SemiBold.otf'}
CHARS = ''.join(chr(c) for c in range(32, 127)) + '·—↗←→●'
_cache = {}

def font_b64(key):
    if key in _cache:
        return _cache[key]
    f = TTFont(FD + FONTS[key])
    opts = subset.Options(); opts.flavor = 'woff'; opts.layout_features = ['kern', 'liga']
    sub = subset.Subsetter(opts); sub.populate(text=CHARS); sub.subset(f)
    buf = io.BytesIO(); f.flavor = 'woff'; f.save(buf)
    _cache[key] = base64.b64encode(buf.getvalue()).decode()
    return _cache[key]

_metric = {}
def width(text, key, size, tracking=0):
    if key not in _metric:
        f = TTFont(FD + FONTS[key]); _metric[key] = (f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm)
    cmap, hmtx, upm = _metric[key]
    w = sum(hmtx[cmap.get(ord(ch), cmap[32])][0] for ch in text)
    return w * size / upm + tracking * size * max(len(text) - 1, 0)

def fontcss(keys):
    fam = {'m': ('IDM', 'normal', 500), 'mi': ('IDM', 'italic', 500), 'sb': ('IDM', 'normal', 600)}
    return ''.join("@font-face{font-family:'%s';font-style:%s;font-weight:%d;src:url(data:font/woff;base64,%s) format('woff')}" % (fam[k] + (font_b64(k),)) for k in keys)

THEMES = {
    'dark':  dict(bg='#00332B', text='#F2F6EF', muted='#C2CEC8', faint='#94A8A1', accent='#96C59E', tabA='#D6D1CB', tabB='#96C59E', ink='#00332B', line='#2A524A', buddyInk='#06201B', pillText='#00332B'),
    'light': dict(bg='#EFEDE8', text='#00332B', muted='#335C55', faint='#5C7A73', accent='#00594A', tabA='#DEDAD2', tabB='#A8D5AE', ink='#00332B', line='#CFCBC3', buddyInk='#00332B', pillText='#00332B'),
}

LOGO = open(os.path.join(os.path.dirname(__file__), 'logo_path.txt')).read().strip()

def svg(w, h, body, keys=('m', 'mi', 'sb'), extra_css='', title=''):
    css = fontcss(keys) + "text{font-family:'IDM',sans-serif}" + extra_css
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-label="%s">'
            '<style>%s</style>%s</svg>') % (w, h, w, h, title, css, body)

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def tab(x, y, w, h, fill, label, color, r=16, size=13, left_square=False):
    rl = 0 if left_square else r
    path = 'M%s %s V%s Q%s %s %s %s H%s Q%s %s %s %s V%s Z' % (x, y + h, y + rl, x, y, x + rl, y, x + w - r, x + w, y, x + w, y + r, y + h)
    return ('<path d="%s" fill="%s"/>' % (path, fill) +
            '<text x="%s" y="%s" text-anchor="middle" font-size="%s" font-weight="600" letter-spacing="1.1" fill="%s">%s</text>' % (x + w / 2, y + h / 2 + size * 0.36, size, color, esc(label)))

BUDDY_RECTS = [(1,1,7,3,'ink'),(0,2,1,13,'ink'),(1,3,15,12,'ink'),(1,2,6,2,'tab'),(1,4,14,10,'body'),(1,4,14,1,'hi'),(1,13,14,1,'shade'),
               (3,10,1,1,'cheek'),(12,10,1,1,'cheek'),(3,15,2,2,'ink'),(11,15,2,2,'ink')]
HAPPY = [(4,8,1,1),(5,7,1,1),(6,8,1,1),(9,8,1,1),(10,7,1,1),(11,8,1,1),(6,10,1,1),(7,11,2,1),(9,10,1,1)]
DOTS = [(5,7,1,2),(10,7,1,2)]
SMILE = [(6,10,1,1),(7,11,2,1),(9,10,1,1)]

def buddy(x, y, px, T, mode='idle'):
    cols = {'ink': T['buddyInk'], 'tab': T['tabA'] if T is THEMES['dark'] else '#FFFFFF', 'body': T['tabB'], 'hi': '#FFFFFF', 'shade': T['buddyInk'], 'cheek': T['buddyInk']}
    ops = {'hi': 0.4, 'shade': 0.18, 'cheek': 0.25}
    r = ''.join('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"%s/>' % (a, b, c, d, cols[k], (' opacity="%s"' % ops[k]) if k in ops else '') for a, b, c, d, k in BUDDY_RECTS)
    if mode == 'wave':
        face = ''.join('<rect x="%d" y="%d" width="%d" height="%d"/>' % f for f in HAPPY)
        arm = '<g class="arm"><rect x="15" y="3" width="3" height="7" fill="%s"/><rect x="16" y="4" width="1" height="5" fill="%s"/></g>' % (cols['ink'], cols['body'])
        inner = arm + r + '<g fill="%s">%s</g>' % (cols['ink'], face)
        cls = ''
    else:
        face = '<g class="blink">%s</g>' % ''.join('<rect x="%d" y="%d" width="%d" height="%d"/>' % f for f in DOTS) + ''.join('<rect x="%d" y="%d" width="%d" height="%d"/>' % f for f in SMILE)
        inner = r + '<g fill="%s">%s</g>' % (cols['ink'], face)
        cls = ' class="bounce"'
    return '<g transform="translate(%s %s) scale(%s)" shape-rendering="crispEdges"><g%s>%s</g></g>' % (x, y, px, cls, inner)

BUDDY_CSS = ('.bounce{transform-box:fill-box;transform-origin:50% 100%;animation:b 1.8s ease-in-out infinite}'
             '@keyframes b{0%,100%{transform:translateY(0) scale(1,1)}12%{transform:translateY(0) scale(1.1,.9)}40%{transform:translateY(-3px) scale(.95,1.06)}58%{transform:translateY(-3px) scale(1,1)}88%{transform:translateY(0) scale(1.06,.94)}}'
             '.blink{animation:k 4s steps(1) infinite}@keyframes k{0%,92%,100%{opacity:1}95%{opacity:0}}'
             '.arm{transform-box:fill-box;transform-origin:0% 100%;animation:w .5s ease-in-out infinite alternate}@keyframes w{from{transform:rotate(-12deg)}to{transform:rotate(28deg)}}'
             '@media (prefers-reduced-motion:reduce){.bounce,.blink,.arm{animation:none}}')

def logo(x, y, size, color, bloom=True):
    s = size / 400
    g = '<path transform="rotate(-18 200 200)" d="%s"/>' % LOGO
    if bloom:
        g = '<path transform="rotate(72 200 200)" d="%s" opacity="0.42"/>' % LOGO + g
    return '<g transform="translate(%s %s) scale(%s)" fill="%s">%s</g>' % (x, y, s, color, g)

def header(T):
    W, H = 1200, 460
    b = '<rect width="%d" height="%d" rx="28" fill="%s"/>' % (W, H, T['bg'])
    b += '<clipPath id="c"><rect width="%d" height="%d" rx="28"/></clipPath><g clip-path="url(#c)">' % (W, H)
    b += tab(744, 0, 220, 40, T['tabA'], '( BOTS & TOOLS )', T['ink']) + '<rect x="744" y="40" width="456" height="70" fill="%s"/>' % T['tabA']
    b += tab(408, 34, 200, 40, T['tabB'], '( BOOKINGS )', T['ink']) + '<rect x="408" y="74" width="792" height="70" fill="%s"/>' % T['tabB']
    b += tab(0, 70, 220, 40, T['tabA'], '( WEBSITES )', T['ink'], left_square=True) + '<rect x="0" y="110" width="1200" height="70" fill="%s"/>' % T['tabA']
    b += tab(0, 116, 190, 40, T['bg'], '( 2026 )', T['text'], left_square=True) + '<rect x="0" y="156" width="1200" height="400" fill="%s"/>' % T['bg']
    b += logo(56, 196, 60, T['accent'])
    b += ('<text x="1144" y="216" text-anchor="end" font-size="15" font-weight="600" letter-spacing="1.3" fill="%s">WEB DEVELOPER</text>'
          '<text x="1144" y="238" text-anchor="end" font-size="15" font-weight="600" letter-spacing="1.3" fill="%s">WEBSITES · BOOKINGS · BOTS</text>') % (T['muted'], T['muted'])
    size = 140; x0 = 50; base = 392
    w1 = width('simba.', 'm', size, -0.045)
    b += '<text x="%d" y="%d" font-size="%d" font-weight="500" letter-spacing="%.1f" fill="%s">simba.<tspan font-style="italic">codes</tspan></text>' % (x0, base, size, -0.045 * size, T['accent'])
    pw = 214
    b += '<rect x="%d" y="352" width="%d" height="42" rx="21" fill="%s"/>' % (1144 - 92 - 18 - pw, pw, T['tabB'])
    b += '<circle cx="%d" cy="373" r="4.5" fill="%s"/>' % (1144 - 92 - 18 - pw + 22, T['pillText'])
    b += '<text x="%d" y="379" font-size="16" font-weight="600" fill="%s">Open for projects</text>' % (1144 - 92 - 18 - pw + 38, T['pillText'])
    b += buddy(1144 - 64, 326, 4, T) + '</g>'
    return svg(W, H, b, extra_css=BUDDY_CSS, title='simba.codes — web developer')

def section(T, num, title, italic, right):
    W, H = 1200, 120
    b = tab(0, 20, 210, 40, T['tabB'], '( %s )' % num, T['ink'], left_square=False)
    b += '<rect x="0" y="60" width="1200" height="6" fill="%s"/>' % T['tabB']
    b += '<text x="0" y="112" font-size="0">.</text>'
    size = 44
    b = '<rect width="%d" height="%d" fill="none"/>' % (W, H) + b
    b += '<text x="240" y="52" font-size="%d" font-weight="500" letter-spacing="%.1f" fill="%s">%s<tspan font-style="italic">%s</tspan></text>' % (size, -0.03 * size, T['text'], esc(title), esc(italic))
    b += '<text x="1200" y="48" text-anchor="end" font-size="13" font-weight="600" letter-spacing="1.1" fill="%s">%s</text>' % (T['faint'], esc(right))
    return svg(W, 72, b, title=title + italic)

def wrap(text, key, size, maxw):
    words, lines, cur = text.split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if width(t, key, size) > maxw and cur:
            lines.append(cur); cur = wd
        else:
            cur = t
    lines.append(cur)
    return lines

def card(T, fill, label, meta, title, blurb, cta):
    W, H = 588, 360
    b = tab(0, 0, width(label, 'sb', 12, 0.09) + 48, 40, fill, label, T['ink'], size=12)
    b += '<path d="M0 40 H%d Q%d 40 %d 64 V%d Q%d %d %d %d H24 Q0 %d 0 %d Z" fill="%s"/>' % (W - 24, W, W, H - 24, W, H, W - 24, H, H, H - 24, fill)
    b += '<text x="32" y="82" font-size="12" font-weight="600" letter-spacing="1.1" fill="%s" opacity="0.7">%s</text>' % (T['ink'], esc(meta))
    b += '<text x="30" y="214" font-size="60" font-weight="500" letter-spacing="-2" fill="%s">%s</text>' % (T['ink'], esc(title))
    for i, ln in enumerate(wrap(blurb, 'm', 19, W - 64)[:2]):
        b += '<text x="32" y="%d" font-size="19" fill="%s">%s</text>' % (256 + i * 27, T['ink'], esc(ln))
    b += '<text x="32" y="330" font-size="14" font-weight="600" letter-spacing="0.6" fill="%s">%s</text>' % (T['ink'], esc(cta))
    return svg(W, H, b, title=title)

def stack(T):
    W, H = 1200, 230
    names = ['TypeScript', 'React', 'Next.js', 'Node', 'Python', 'Rust', 'Postgres', 'Docker', 'Figma']
    size = 60; b = ''
    def adv(k, name, last):
        key = 'mi' if k % 2 else 'm'
        a = width(name, key, size, -0.04) + 34
        if not last:
            a += width('/', 'm', size) + 22
        return a
    rows, cur, curw = [], [], 0
    for k, name in enumerate(names):
        a = adv(k, name, k == len(names) - 1)
        if cur and curw + a > W:
            rows.append(cur); cur, curw = [], 0
        cur.append((k, name)); curw += a
    rows.append(cur)
    for r, row in enumerate(rows):
        x = 0; y = 72 + r * 80
        for k, name in row:
            key = 'mi' if k % 2 else 'm'
            col = T['accent'] if k == 0 else T['text']
            b += '<text x="%.1f" y="%d" font-size="%d" font-weight="500" letter-spacing="%.1f" fill="%s"%s>%s</text>' % (x, y, size, -0.04 * size, col, ' font-style="italic"' if k % 2 else '', esc(name))
            x += width(name, key, size, -0.04) + 14
            b += '<text x="%.1f" y="%d" font-size="13" font-weight="600" fill="%s">0%d</text>' % (x - 6, y - 38, T['faint'], k + 1)
            x += 20
            if k != len(names) - 1:
                b += '<text x="%.1f" y="%d" font-size="%d" font-weight="500" fill="%s">/</text>' % (x, y, size, T['line'])
                x += width('/', 'm', size) + 22
    b += '<rect x="0" y="206" width="1200" height="1" fill="%s"/>' % T['line']
    b += '<text x="0" y="228" font-size="13" font-weight="600" letter-spacing="1.1" fill="%s">( 09 TOOLS · ONE WAY OF WORKING: SHIP IT PROPERLY )</text>' % T['faint']
    return svg(W, H + 6, b, title='TypeScript, React, Next.js, Node, Python, Rust, Postgres, Docker, Figma')

def footer(T):
    W, H = 1200, 320
    b = '<path d="M0 32 Q0 0 32 0 H1168 Q1200 0 1200 32 V%d H0 Z" fill="%s"/>' % (H, T['tabB'])
    b += '<text x="56" y="76" font-size="13" font-weight="600" letter-spacing="1.1" fill="%s">( CONTACT )</text>' % T['ink']
    b += '<text x="50" y="178" font-size="96" font-weight="500" letter-spacing="-4.3" fill="%s">Let\'s start <tspan font-style="italic">a folder.</tspan></text>' % T['ink']
    b += '<text x="56" y="246" font-size="30" font-weight="500" fill="%s">contact@simba.codes</text>' % T['ink']
    b += '<rect x="56" y="256" width="%.1f" height="2" fill="%s"/>' % (width('contact@simba.codes', 'm', 30), T['ink'])
    b += '<rect x="56" y="282" width="1088" height="1" fill="%s" opacity="0.25"/>' % T['ink']
    b += '<text x="56" y="306" font-size="13" font-weight="600" letter-spacing="1.1" fill="%s" opacity="0.8">© 2026 SIMBA</text>' % T['ink']
    b += '<text x="1144" y="306" text-anchor="end" font-size="13" font-weight="600" letter-spacing="1.1" fill="%s" opacity="0.8">SIMBA.CODES ↗</text>' % T['ink']
    bt = dict(T); bt['tabB'] = '#FFFFFF' if T is THEMES['light'] else '#D6D1CB'
    b += buddy(1144 - 80, 160, 5, bt, mode='wave')
    return svg(W, H, b, extra_css=BUDDY_CSS, title="Let's start a folder — contact@simba.codes")

for mode, T in THEMES.items():
    def w(name, s):
        open(os.path.join(OUT, '%s-%s.svg' % (name, mode)), 'w').write(s)
    w('header', header(T))
    w('section-about', section(T, '01', 'About ', 'me', 'WHO’S BEHIND THE FOLDERS'.replace('’', "'")))
    w('section-work', section(T, '02', 'Selected ', 'work', 'PROJECT COMPILATION · VOL. 1'))
    w('section-stack', section(T, '03', 'My st', 'ack', 'INDEX 01 — 09'))
    w('card-corner23rd', card(T, T['tabA'], '( WEBSITE · BOOKINGS )', '2026 · LIVE', 'Corner 23rd', 'A website for a Johannesburg tailoring and embroidery house, with fittings booked online.', 'VIEW PROJECT ↗'))
    w('card-once', card(T, T['tabB'], '( WEBSITE · BOOKINGS )', '2026 · IN PROGRESS', 'ONCE', 'A booking-ready website for a chef-led private dining brand in Johannesburg.', 'VIEW PROJECT ↗'))
    w('card-rawcord', card(T, T['tabB'], '( OPEN SOURCE )', 'DISCORD · SQLITE', 'Rawcord', 'A zero-dependency Discord bot template built straight on the raw Discord API.', 'VIEW REPO ↗'))
    w('card-next', card(T, T['tabA'], '( NEXT PROJECT )', 'YOURS?', 'Your business', 'Websites, booking systems and custom tools. Let’s build something.'.replace('’', "'"), 'GET IN TOUCH ↗'))
    w('stack', stack(T))
    w('footer', footer(T))
print('done')
