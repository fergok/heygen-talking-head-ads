"""TikTok 'Reply to … comment' bubble, rebuilt from the user's screenshot (ref.png, 684 px wide) at 1080 px video scale."""
import sys
from PIL import Image, ImageDraw, ImageFont
import os
REF = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref.png")).convert("RGB")
GREY = 21.4                  # 'Reply to …' line, screenshot px
K = 1080 / 684 * 2            # screenshot px -> video px, drawn at 2x then halved
HN = "/System/Library/Fonts/HelveticaNeue.ttc"   # index 1 Bold matches TikTok's comment text
bold = ImageFont.truetype(HN, round(30.5 * K), index=1)
grey = ImageFont.truetype(HN, round(GREY * K), index=0)
text = sys.argv[1] if len(sys.argv) > 1 else "Red lights please…for all us astronomers"
user = "Grace_Shares"
s = lambda v: round(v * K)
# wrap the comment to the screenshot's text column (x 205 to ~566)
words, lines, cur = text.split(), [], ""
for w in words:
    t = (cur + " " + w).strip()
    if bold.getlength(t) <= s(361) or not cur: cur = t
    else: lines.append(cur); cur = w
lines.append(cur)
top, left, right = 248, 114, 579
lh = 41.3                                   # comment line pitch
first = 330                               # first comment baseline
bottom = first + lh * (len(lines) - 1) + 38
W, H = s(right - left + 4), s(bottom - top + 26)
im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
ox, oy = s(left), s(top)
P = lambda x, y: (s(x) - ox, s(y) - oy)
d.rounded_rectangle([P(left, top), P(right, bottom)], radius=s(9), fill="white")
d.polygon([P(left, bottom - 4), P(left + 26, bottom - 1), P(left + 1, bottom + 26)], fill="white")   # tail, bottom left
# avatar: the circle from the screenshot
cx, cy, r = 161, 316, 27.5
av = REF.crop((round(cx - r), round(cy - r), round(cx + r), round(cy + r))).resize((s(2 * r), s(2 * r)), Image.LANCZOS)
m = Image.new("L", av.size, 0); ImageDraw.Draw(m).ellipse([0, 0, av.size[0] - 1, av.size[1] - 1], fill=255)
im.paste(av, P(cx - r, cy - r), m)
d.text(P(205, 287), f"Reply to {user}'s comment", font=grey, fill=(105, 105, 105), anchor="ls")
for i, l in enumerate(lines):
    d.text(P(205, first + lh * i), l, font=bold, fill=(22, 22, 22), anchor="ls")
im = im.resize((W // 2, H // 2), Image.LANCZOS)
im.save(sys.argv[2] if len(sys.argv) > 2 else "reply.png")
print(lines, im.size)
