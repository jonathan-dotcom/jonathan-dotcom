"""Draw the profile's little pixel desk. Requires Pillow; no external assets.

Run: python scripts/draw_desk.py
The 176 x 88 pixel canvas is scaled with nearest-neighbour interpolation.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from PIL.GifImagePlugin import GifImageFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
COLORS = [
    '#ff00ff',  # transparent index
    '#514b46',  # outline
    '#87796c',  # shadow
    '#b4a38c',  # midtone
    '#dbcbb0',  # warm case
    '#f3e6ce',  # highlight
    '#263e3b',  # screen
    '#466055',  # foliage shadow
    '#77906b',  # foliage
    '#afbe88',  # screen phosphor
    '#bf7958',  # terracotta
    '#e5ae83',  # terracotta highlight
    '#b9b2a4',  # steam
]
palette = [v for color in COLORS for v in bytes.fromhex(color[1:])]
palette += [0] * (768 - len(palette))


def draw_frame(tick):
    im = Image.new('P', (176, 88), 0)
    im.putpalette(palette)
    d = ImageDraw.Draw(im)

    def r(box, color):
        d.rectangle(box, fill=color)

    # A single stepped desk edge; keep the rest transparent.
    r((18, 70, 158, 71), 2)
    r((21, 72, 155, 73), 1)
    r((25, 74, 28, 80), 2)
    r((148, 74, 151, 80), 2)

    # Sprout in a small terracotta pot.
    r((34, 46, 35, 58), 7)
    r((28, 42, 32, 46), 8)
    r((31, 45, 34, 48), 8)
    r((36, 38, 41, 41), 8)
    r((35, 41, 38, 44), 8)
    r((39, 38, 41, 39), 9)
    r((26, 55, 43, 58), 1)
    r((27, 55, 42, 57), 11)
    r((29, 59, 40, 67), 10)
    r((31, 68, 38, 69), 1)
    r((29, 59, 31, 65), 11)
    r((39, 59, 40, 67), 2)

    # Chunky CRT case, stepped corners and two-pixel bevels.
    r((62, 17, 113, 18), 1)
    r((60, 19, 115, 53), 1)
    r((62, 54, 113, 56), 1)
    r((62, 19, 111, 52), 4)
    r((62, 19, 110, 20), 5)
    r((62, 21, 63, 51), 5)
    r((112, 20, 114, 52), 3)
    r((64, 53, 111, 54), 3)
    r((68, 24, 106, 45), 2)
    r((70, 26, 104, 43), 6)
    r((70, 26, 103, 27), 1)
    r((71, 49, 85, 49), 3)
    r((103, 49, 105, 50), 8)
    r((77, 57, 99, 61), 2)
    r((79, 57, 97, 60), 3)
    r((72, 62, 105, 64), 1)
    r((74, 62, 103, 63), 4)

    # A tiny lowercase 'jab' drawn on a 3 x 5 grid.
    glyphs = {'j': ['001', '000', '001', '101', '111'],
              'a': ['000', '110', '001', '111', '111'],
              'b': ['100', '100', '110', '101', '110']}
    for i, letter in enumerate('jab'):
        for y, row in enumerate(glyphs[letter]):
            for x, value in enumerate(row):
                if value == '1':
                    r((78 + i * 5 + x, 32 + y, 78 + i * 5 + x, 32 + y), 9)
    if tick % 12 < 7:
        r((94, 36, 97, 36), 9)

    # Low keyboard, not another block of content.
    r((64, 66, 110, 69), 1)
    r((66, 66, 108, 68), 4)
    for x in range(69, 105, 5):
        r((x, 67, x + 2, 67), 2)

    # Small mug with just a few changing steam pixels.
    r((120, 57, 130, 58), 5)
    r((120, 59, 130, 67), 10)
    r((120, 68, 130, 69), 1)
    r((121, 59, 122, 65), 11)
    r((131, 59, 134, 60), 10)
    r((133, 61, 134, 64), 10)
    r((131, 65, 134, 66), 10)
    phase = (tick // 4) % 6
    for x, y in [(123, 52), (127, 47)]:
        dx = [0, 0, 1, 1, 0, -1][phase]
        dy = [0, -1, -2, -1, 0, 1][phase]
        r((x + dx, y + dy, x + dx, y + dy + 2), 12)

    # A copper asterisk, like a tiny pencil annotation, not a star field.
    r((132, 25, 132, 31), 10)
    r((129, 28, 135, 28), 10)
    if 30 <= tick < 36:
        r((137, 22, 137, 22), 11)

    return im.resize((704, 352), Image.Resampling.NEAREST)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    frames = [draw_frame(tick) for tick in range(48)]
    still = frames[0].copy()
    still.info['transparency'] = 0
    still.convert('RGBA').save(OUT / 'little-desk.png')
    frames[0].save(
        OUT / 'little-desk.gif', save_all=True, append_images=frames[1:],
        duration=150, loop=0, transparency=0, disposal=2, optimize=False,
    )
    with Image.open(OUT / 'little-desk.gif') as gif:
        assert isinstance(gif, GifImageFile)
        duration = 0
        for i in range(gif.n_frames):
            gif.seek(i)
            duration += gif.info['duration']
        print(f'GIF: {gif.size}, {gif.n_frames} frames, {duration} ms loop')
    print('Wrote assets/little-desk.gif and assets/little-desk.png')
