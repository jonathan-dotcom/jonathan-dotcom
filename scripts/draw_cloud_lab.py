"""Draw the profile's pixel-art cloud lab with Pillow and no external assets.

Run: python scripts/draw_cloud_lab.py
The 176 x 88 canvas uses a fixed palette and nearest-neighbour scaling.
The terminal is an illustrative build/deploy/health-check loop, not telemetry.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from PIL.GifImagePlugin import GifImageFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
COLORS = [
    '#ff00ff',  # transparent index, never a visible background
    '#514b46', '#87796c', '#b4a38c', '#dbcbb0', '#f3e6ce',
    '#263e3b', '#466055', '#77906b', '#afbe88',
    '#bf7958', '#e5ae83', '#b9b2a4',
]
PALETTE = [v for color in COLORS for v in bytes.fromhex(color[1:])]
PALETTE += [0] * (768 - len(PALETTE))
GLYPHS = {
    '>': ['100', '010', '001', '010', '100'],
    'b': ['100', '100', '110', '101', '110'],
    'u': ['000', '101', '101', '101', '111'],
    'i': ['010', '000', '010', '010', '010'],
    'l': ['100', '100', '100', '100', '110'],
    'd': ['001', '001', '011', '101', '011'],
    'e': ['000', '111', '110', '100', '111'],
    'p': ['000', '110', '101', '110', '100'],
    'o': ['000', '111', '101', '101', '111'],
    'y': ['000', '101', '111', '001', '110'],
    'c': ['000', '111', '100', '100', '111'],
    'h': ['100', '100', '110', '101', '101'],
    'k': ['100', '101', '110', '110', '101'],
}


def draw_frame(tick):
    im = Image.new('P', (176, 88), 0)
    im.putpalette(PALETTE)
    d = ImageDraw.Draw(im)
    stage, progress = divmod(tick % 72, 24)

    def r(box, color):
        d.rectangle(box, fill=color)

    def text(label, x, y, color=9):
        for index, letter in enumerate(label):
            for row, bits in enumerate(GLYPHS[letter]):
                for col, value in enumerate(bits):
                    if value == '1':
                        d.point((x + index * 4 + col, y + row), fill=color)

    # Preserve the original desk, sprout, warm CRT, keyboard, and mug.
    for box, color in [
        ((18,70,158,71),2), ((21,72,155,73),1),
        ((25,74,28,80),2), ((148,74,151,80),2),
        ((34,46,35,58),7), ((28,42,32,46),8),
        ((31,45,34,48),8), ((36,38,41,41),8),
        ((35,41,38,44),8), ((39,38,41,39),9),
        ((26,55,43,58),1), ((27,55,42,57),11),
        ((29,59,40,67),10), ((31,68,38,69),1),
        ((29,59,31,65),11), ((39,59,40,67),2),
        ((62,17,113,18),1), ((60,19,115,53),1),
        ((62,54,113,56),1), ((62,19,111,52),4),
        ((62,19,110,20),5), ((62,21,63,51),5),
        ((112,20,114,52),3), ((64,53,111,54),3),
        ((68,24,106,45),2), ((70,26,104,43),6),
        ((70,26,103,27),1), ((71,49,85,49),3),
        ((103,49,105,50),8), ((77,57,99,61),2),
        ((79,57,97,60),3), ((72,62,105,64),1),
        ((74,62,103,63),4), ((64,66,110,69),1),
        ((66,66,108,68),4), ((120,57,130,58),5),
        ((120,59,130,67),10), ((120,68,130,69),1),
        ((121,59,122,65),11), ((131,59,134,60),10),
        ((133,61,134,64),10), ((131,65,134,66),10),
    ]:
        r(box, color)
    for x in range(69, 105, 5):
        r((x,67,x+2,67),2)

    # The cloud is one stepped silhouette, in the existing quiet palette.
    for box in [(139,18,161,23), (143,15,157,23), (147,12,153,23)]:
        r(box, 2)
    for box in [(140,19,160,22), (144,16,156,22), (148,13,152,22)]:
        r(box, 4)
    r((145,16,149,16), 5)
    r((148,13,152,13), 5)

    # Three small server units rest on the desk, not a dashboard panel.
    r((140,37,156,69),1)
    r((141,38,154,68),3)
    r((155,38,156,68),2)
    for index, y in enumerate([40,49,58]):
        r((142,y,153,y+6),6)
        r((143,y+1,151,y+1),2)
        r((143,y+4,147,y+4),3)
        lit = stage == 2 or (tick + index * 4) % 18 < 3
        r((151,y+4,152,y+5),9 if lit else 7)
    r((142,67,153,68),2)

    # Short legible 3x5 terminal labels. "check" denotes a health check.
    label = ['build','deploy','check'][stage]
    text('>',72,31)
    text(label,78,31)
    if tick % 12 < 7:
        cursor = 78 + len(label) * 4
        r((cursor,35,cursor+1,35),9)
    if stage == 2 and progress >= 12:
        text('ok',83,38)
        d.line([(75,40),(77,42),(80,38)],fill=9,width=1)
    else:
        filled = min(6, progress // 3)
        for index in range(6):
            r((73+index*5,40,75+index*5,41),9 if index < filled else 7)

    # A single occasional packet follows an orthogonal cloud/rack route.
    if stage == 1 and progress < 18:
        # Keep the packet in the actual gap between cloud and server rack.
        route = [(149,25+i) for i in range(10)]
        index = round(progress * (len(route)-1) / 17)
        x,y = route[index]
        # One solid packet with a shadow edge, not separated trail pixels.
        r((x,y,x+3,y+2),7)
        r((x,y,x+2,y+1),9)

    # Slow two-pixel steam motion; period divides the complete loop.
    phase = (tick // 4) % 6
    for x,y in [(123,52),(127,47)]:
        dx = [0,0,1,1,0,-1][phase]
        dy = [0,-1,-2,-1,0,1][phase]
        r((x+dx,y+dy,x+dx,y+dy+2),12)
    return im.resize((704,352),Image.Resampling.NEAREST)


def rgba(frame):
    frame = frame.copy()
    frame.info['transparency'] = 0
    return frame.convert('RGBA')


def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    frames = [draw_frame(tick) for tick in range(72)]
    rgba(frames[60]).save(OUT / 'cloud-lab.png')
    frames[0].save(
        OUT / 'cloud-lab.gif',save_all=True,append_images=frames[1:],
        duration=150,loop=0,transparency=0,disposal=2,optimize=False,
    )
    with Image.open(OUT / 'cloud-lab.gif') as gif:
        assert isinstance(gif, GifImageFile)
        assert gif.size == (704,352)
        # Pillow merges identical held frames; total playback time is invariant.
        encoded_frames = gif.n_frames
        assert encoded_frames >= 24
        assert gif.info['loop'] == 0
        total = 0
        for index in range(encoded_frames):
            gif.seek(index)
            total += gif.info['duration']
            assert gif.convert('RGBA').getchannel('A').getpixel((0,0)) == 0
        assert total == 10800
    still = Image.open(OUT / 'cloud-lab.png')
    assert still.mode == 'RGBA' and still.getchannel('A').getpixel((0,0)) == 0
    assert len(set(frame.tobytes() for frame in frames)) >= 24
    # Review sheet uses the real GitHub light/dark backgrounds at display size.
    sheet = Image.new('RGB',(1056,424),'#f6f8fa')
    for row,background in enumerate(['#ffffff','#0d1117']):
        for col,tick in enumerate([8,32,60]):
            panel = Image.new('RGBA',(352,212),background)
            panel.alpha_composite(rgba(frames[tick]).resize((352,176),Image.Resampling.NEAREST),(0,20))
            sheet.paste(panel.convert('RGB'),(col*352,row*212))
    sheet.save(ROOT / 'cloud-lab-review.png')
    print(f'GIF verified: {encoded_frames} encoded frames, {total} ms, {(OUT / "cloud-lab.gif").stat().st_size} bytes')
    print('PNG verified: RGBA with transparent background')
    print('Review sheet:',ROOT / 'cloud-lab-review.png')


if __name__ == '__main__':
    generate()
