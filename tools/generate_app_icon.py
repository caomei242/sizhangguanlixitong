from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "private_ledger" / "assets" / "app_icon.png"


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def main() -> None:
    scale = 3
    size = 1024
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    def s(value: int) -> int:
        return value * scale

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (s(80), s(82), s(944), s(946)),
        radius=s(212),
        fill=(48, 71, 118, 56),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(s(26)))
    canvas.alpha_composite(shadow)

    rounded(draw, (s(70), s(62), s(954), s(946)), s(212), "#eef7ff")
    rounded(draw, (s(154), s(154), s(870), s(870)), s(118), "#ffffff")
    rounded(draw, (s(230), s(226), s(794), s(804)), s(86), "#f5f8ff")
    rounded(draw, (s(230), s(226), s(794), s(372)), s(86), "#4e7af6")
    draw.rectangle((s(230), s(324), s(794), s(372)), fill="#4e7af6")
    draw.ellipse((s(314), s(180), s(370), s(236)), fill="#f8be4a")
    draw.ellipse((s(652), s(180), s(708), s(236)), fill="#f8be4a")
    for x in [316, 468, 620]:
        for y in [442, 556, 670]:
            rounded(draw, (s(x), s(y), s(x + 92), s(y + 76)), s(24), "#dbe6ff")
    rounded(draw, (s(616), s(550), s(716), s(636)), s(28), "#ff8aa0")
    draw.line((s(662), s(594), s(690), s(622)), fill="#ffffff", width=s(12))
    draw.line((s(690), s(622), s(730), s(570)), fill="#ffffff", width=s(12))

    draw.ellipse((s(676), s(746), s(848), s(918)), fill="#ff4f72")
    draw.ellipse((s(700), s(774), s(824), s(916)), fill="#ff597b")
    for x, y in [(722, 804), (770, 798), (806, 836), (734, 858), (774, 890)]:
        draw.ellipse((s(x - 8), s(y - 8), s(x + 8), s(y + 8)), fill="#ffd8e0")
    draw.polygon([(s(734), s(746)), (s(776), s(696)), (s(800), s(760))], fill="#25ab57")
    draw.polygon([(s(774), s(744)), (s(844), s(706)), (s(810), s(774))], fill="#239d50")
    draw.polygon([(s(710), s(748)), (s(674), s(704)), (s(744), s(720))], fill="#30b965")

    icon = canvas.resize((size, size), Image.Resampling.LANCZOS)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    icon.save(OUTPUT)


if __name__ == "__main__":
    main()
