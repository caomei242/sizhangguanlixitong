from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "icon-options"
SIZE = 1024
SCALE = 3


def s(value: int) -> int:
    return value * SCALE


def make_canvas(bg: str = "#eef3ff", inner: str = "#ffffff") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    canvas = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (s(78), s(82), s(946), s(950)),
        radius=s(212),
        fill=(44, 64, 108, 58),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(s(26)))
    canvas.alpha_composite(shadow)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((s(68), s(60), s(956), s(948)), radius=s(214), fill=bg)
    draw.rounded_rectangle((s(152), s(152), s(872), s(872)), radius=s(118), fill=inner)
    return canvas, draw


def save(canvas: Image.Image, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    icon = canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    icon.save(OUT_DIR / f"{name}.png")


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def strawberry(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    draw.ellipse((s(cx - r), s(cy - r), s(cx + r), s(cy + r)), fill="#ff4f72")
    draw.ellipse((s(cx - r // 2), s(cy - r // 3), s(cx + r // 2), s(cy + r)), fill="#ff5b7c")
    for dx, dy in [(-20, -24), (22, -30), (44, 10), (-8, 42), (24, 62)]:
        seed = max(5, r // 14)
        draw.ellipse(
            (s(cx + dx - seed), s(cy + dy - seed), s(cx + dx + seed), s(cy + dy + seed)),
            fill="#ffd8df",
        )
    draw.polygon([(s(cx - 18), s(cy - r)), (s(cx + 34), s(cy - r - 52)), (s(cx + 46), s(cy - r + 10))], fill="#27ab58")
    draw.polygon([(s(cx + 18), s(cy - r)), (s(cx + 86), s(cy - r - 36)), (s(cx + 64), s(cy - r + 26))], fill="#20994c")
    draw.polygon([(s(cx - 34), s(cy - r + 4)), (s(cx - 74), s(cy - r - 34)), (s(cx + 2), s(cy - r - 16))], fill="#31ba64")


def donut(draw: ImageDraw.ImageDraw, cx: int, cy: int, outer_r: int, inner_r: int) -> None:
    box = (s(cx - outer_r), s(cy - outer_r), s(cx + outer_r), s(cy + outer_r))
    draw.pieslice(box, start=198, end=318, fill="#ff5a7b")
    draw.pieslice(box, start=318, end=24, fill="#4e7af6")
    draw.pieslice(box, start=24, end=198, fill="#f8be4a")
    draw.ellipse((s(cx - inner_r), s(cy - inner_r), s(cx + inner_r), s(cy + inner_r)), fill="#ffffff")


def option_a_ledger_ring() -> None:
    canvas, draw = make_canvas("#eef3ff", "#ffffff")
    rounded(draw, (s(224), s(222), s(792), s(804)), s(74), "#f5f8ff")
    rounded(draw, (s(246), s(248), s(324), s(778)), s(38), "#4e7af6")
    rounded(draw, (s(364), s(290), s(610), s(344)), s(28), "#c8d7fb")
    rounded(draw, (s(364), s(384), s(680), s(430)), s(23), "#d8e4ff")
    rounded(draw, (s(364), s(460), s(636), s(506)), s(23), "#d8e4ff")
    rounded(draw, (s(364), s(584), s(448), s(652)), s(34), "#4e7af6")
    rounded(draw, (s(474), s(584), s(558), s(652)), s(34), "#6bc29f")
    rounded(draw, (s(584), s(584), s(668), s(652)), s(34), "#f8be4a")
    donut(draw, 618, 638, 120, 54)
    strawberry(draw, 748, 834, 86)
    save(canvas, "A-ledger-ring")


def option_b_wallet_budget() -> None:
    canvas, draw = make_canvas("#fff2f6", "#ffffff")
    rounded(draw, (s(224), s(324), s(800), s(742)), s(92), "#4e7af6")
    rounded(draw, (s(228), s(374), s(796), s(742)), s(88), "#5c85f7")
    rounded(draw, (s(512), s(430), s(826), s(610)), s(60), "#f4f7ff")
    draw.ellipse((s(718), s(488), s(780), s(550)), fill="#f8be4a")
    rounded(draw, (s(272), s(246), s(640), s(404)), s(70), "#f7c7d4")
    rounded(draw, (s(304), s(274), s(600), s(330)), s(24), "#ffffff")
    rounded(draw, (s(304), s(356), s(528), s(408)), s(24), "#ffe0e7")
    strawberry(draw, 722, 770, 80)
    save(canvas, "B-wallet-budget")


def option_c_calendar_reminder() -> None:
    canvas, draw = make_canvas("#eef7ff", "#ffffff")
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
    strawberry(draw, 738, 824, 80)
    save(canvas, "C-calendar-reminder")


def option_d_account_stack() -> None:
    canvas, draw = make_canvas("#f2f6ff", "#ffffff")
    rounded(draw, (s(250), s(300), s(736), s(720)), s(66), "#dce6ff")
    rounded(draw, (s(202), s(250), s(688), s(670)), s(66), "#edf3ff")
    rounded(draw, (s(258), s(208), s(810), s(692)), s(74), "#ffffff")
    rounded(draw, (s(300), s(270), s(770), s(360)), s(34), "#4e7af6")
    rounded(draw, (s(334), s(430), s(648), s(478)), s(23), "#d8e4ff")
    rounded(draw, (s(334), s(514), s(708), s(562)), s(23), "#d8e4ff")
    rounded(draw, (s(334), s(602), s(486), s(666)), s(30), "#6bc29f")
    rounded(draw, (s(534), s(602), s(684), s(666)), s(30), "#f8be4a")
    rounded(draw, (s(710), s(516), s(804), s(602)), s(28), "#ff8aa0")
    strawberry(draw, 758, 800, 80)
    save(canvas, "D-account-stack")


def option_e_savings_jar() -> None:
    canvas, draw = make_canvas("#eef7f2", "#ffffff")
    rounded(draw, (s(360), s(226), s(654), s(308)), s(34), "#4e7af6")
    rounded(draw, (s(296), s(286), s(720), s(768)), s(126), "#d9e8ff")
    rounded(draw, (s(328), s(320), s(688), s(730)), s(112), "#edf5ff")
    draw.ellipse((s(392), s(410), s(624), s(642)), fill="#f8be4a")
    draw.ellipse((s(420), s(442), s(596), s(618)), fill="#ffd77b")
    rounded(draw, (s(384), s(666), s(632), s(726)), s(30), "#4e7af6")
    rounded(draw, (s(430), s(560), s(494), s(620)), s(20), "#ffffff")
    rounded(draw, (s(532), s(560), s(596), s(620)), s(20), "#ffffff")
    strawberry(draw, 724, 786, 84)
    save(canvas, "E-savings-jar")


def option_f_dashboard_grid() -> None:
    canvas, draw = make_canvas("#f3f1ff", "#ffffff")
    cards = [
        ((246, 246, 492, 474), "#4e7af6"),
        ((532, 246, 778, 474), "#ff8aa0"),
        ((246, 520, 492, 748), "#6bc29f"),
        ((532, 520, 778, 748), "#f8be4a"),
    ]
    for box, color in cards:
        rounded(draw, tuple(s(v) for v in box), s(48), "#f5f8ff")
        rounded(draw, (s(box[0] + 26), s(box[1] + 30), s(box[2] - 26), s(box[1] + 96)), s(28), color)
    rounded(draw, (s(292), s(354), s(446), s(400)), s(22), "#d8e4ff")
    donut(draw, 654, 364, 68, 30)
    rounded(draw, (s(292), s(616), s(446), s(676)), s(28), "#4e7af6")
    for x in [576, 652, 728]:
        draw.ellipse((s(x - 26), s(620 - 26), s(x + 26), s(620 + 26)), fill="#4e7af6")
    strawberry(draw, 746, 816, 78)
    save(canvas, "F-dashboard-grid")


def option_g_binder_tabs() -> None:
    canvas, draw = make_canvas("#eef4ff", "#ffffff")
    rounded(draw, (s(244), s(242), s(788), s(804)), s(74), "#f5f8ff")
    for x, color in [(286, "#4e7af6"), (374, "#6bc29f"), (462, "#f8be4a"), (550, "#ff8aa0")]:
        rounded(draw, (s(x), s(196), s(x + 64), s(260)), s(22), color)
    rounded(draw, (s(290), s(312), s(716), s(366)), s(28), "#d0dcfb")
    rounded(draw, (s(290), s(404), s(650), s(450)), s(23), "#dbe6ff")
    rounded(draw, (s(290), s(486), s(694), s(532)), s(23), "#dbe6ff")
    rounded(draw, (s(290), s(594), s(352), s(654)), s(20), "#4e7af6")
    rounded(draw, (s(388), s(594), s(450), s(654)), s(20), "#6bc29f")
    rounded(draw, (s(486), s(594), s(548), s(654)), s(20), "#f8be4a")
    rounded(draw, (s(584), s(594), s(646), s(654)), s(20), "#ff8aa0")
    strawberry(draw, 742, 808, 78)
    save(canvas, "G-binder-tabs")


def option_h_reminder_lane() -> None:
    canvas, draw = make_canvas("#fff3f7", "#ffffff")
    rounded(draw, (s(228), s(226), s(788), s(806)), s(84), "#f5f8ff")
    draw.line((s(642), s(286), s(642), s(736)), fill="#d7e2fb", width=s(18))
    for y, color in [(322, "#ff8aa0"), (466, "#d7e2fb"), (610, "#d7e2fb")]:
        rounded(draw, (s(606), s(y), s(678), s(y + 68)), s(24), color)
    rounded(draw, (s(284), s(294), s(556), s(346)), s(26), "#c9d8fb")
    rounded(draw, (s(284), s(388), s(596), s(434)), s(22), "#dbe6ff")
    rounded(draw, (s(284), s(472), s(558), s(518)), s(22), "#dbe6ff")
    rounded(draw, (s(284), s(596), s(430), s(664)), s(32), "#4e7af6")
    donut(draw, 518, 634, 112, 50)
    strawberry(draw, 748, 826, 82)
    save(canvas, "H-reminder-lane")


def option_i_balance_target() -> None:
    canvas, draw = make_canvas("#eef6ff", "#ffffff")
    for r, color in [(292, "#edf4ff"), (214, "#dbe7ff"), (136, "#c3d5ff")]:
        draw.ellipse((s(512 - r), s(512 - r), s(512 + r), s(512 + r)), fill=color)
    donut(draw, 512, 512, 158, 74)
    rounded(draw, (s(274), s(716), s(750), s(786)), s(34), "#4e7af6")
    rounded(draw, (s(348), s(250), s(676), s(314)), s(30), "#d0dcfb")
    rounded(draw, (s(392), s(340), s(632), s(390)), s(24), "#dbe6ff")
    rounded(draw, (s(424), s(410), s(600), s(454)), s(22), "#dbe6ff")
    strawberry(draw, 742, 806, 82)
    save(canvas, "I-balance-target")


def contact_sheet() -> None:
    names = [
        ("A", "ledger-ring"),
        ("B", "wallet-budget"),
        ("C", "calendar-reminder"),
        ("D", "account-stack"),
        ("E", "savings-jar"),
        ("F", "dashboard-grid"),
        ("G", "binder-tabs"),
        ("H", "reminder-lane"),
        ("I", "balance-target"),
    ]
    thumb = 220
    padding = 28
    label_h = 38
    sheet_w = padding * 4 + thumb * 3
    sheet_h = padding * 4 + (thumb + label_h) * 3
    sheet = Image.new("RGBA", (sheet_w, sheet_h), "#f5f7fb")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 22)
    except Exception:
        font = ImageFont.load_default()
    for idx, (letter, slug) in enumerate(names):
        row = idx // 3
        col = idx % 3
        x = padding + col * (thumb + padding)
        y = padding + row * (thumb + label_h + padding)
        icon = Image.open(OUT_DIR / f"{letter}-{slug}.png").resize((thumb, thumb), Image.Resampling.LANCZOS)
        sheet.alpha_composite(icon, (x, y))
        draw.text((x + 4, y + thumb + 8), f"{letter}  {slug}", fill="#20304a", font=font)
    sheet.convert("RGB").save(OUT_DIR / "contact-sheet.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    option_a_ledger_ring()
    option_b_wallet_budget()
    option_c_calendar_reminder()
    option_d_account_stack()
    option_e_savings_jar()
    option_f_dashboard_grid()
    option_g_binder_tabs()
    option_h_reminder_lane()
    option_i_balance_target()
    contact_sheet()


if __name__ == "__main__":
    main()
