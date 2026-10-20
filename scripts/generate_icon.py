"""
Icon Generator for ApexClicker Pro.
Generates multi-resolution .ico and high-res transparent .png assets.
"""

import os
from PIL import Image, ImageDraw


def generate_app_icon():
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded rectangle background
    pad = 12
    r = 48
    bg_rect = [pad, pad, size - pad, size - pad]

    # Draw dark glowing background
    draw.rounded_rectangle(
        bg_rect,
        radius=r,
        fill=(24, 24, 37, 255),
        outline=(137, 180, 250, 255),
        width=6,
    )

    # Inner subtle glow outline
    inner_pad = pad + 8
    draw.rounded_rectangle(
        [inner_pad, inner_pad, size - inner_pad, size - inner_pad],
        radius=r - 6,
        outline=(49, 50, 68, 180),
        width=3,
    )

    # Stylized lightning bolt + cursor apex in center
    lightning_pts = [
        (140, 36),   # Top point
        (80, 136),   # Mid left outer
        (124, 136),  # Mid left inner
        (104, 224),  # Bottom point
        (184, 114),  # Mid right outer
        (140, 114),  # Mid right inner
    ]

    # Draw soft neon cyan glow for lightning
    for offset in range(8, 0, -2):
        draw.polygon(lightning_pts, fill=(137, 180, 250, int(35 / offset * 2)))

    # Core lightning bolt with vibrant cyan/blue/white
    draw.polygon(lightning_pts, fill=(137, 180, 250, 255), outline=(205, 214, 244, 255))

    # High-voltage white core streak
    core_pts = [
        (138, 48),
        (96, 130),
        (128, 130),
        (112, 210),
        (170, 120),
        (138, 120),
    ]
    draw.polygon(core_pts, fill=(245, 247, 255, 230))

    # Energy spark nodes
    sparks = [(64, 76, 5), (196, 72, 6), (192, 178, 5), (60, 168, 4)]
    for sx, sy, srad in sparks:
        draw.ellipse(
            [sx - srad, sy - srad, sx + srad, sy + srad],
            fill=(166, 227, 161, 230),
            outline=(255, 255, 255, 255),
        )

    # Save PNG
    png_path = os.path.join(assets_dir, "icon.png")
    img.save(png_path, "PNG")

    # Save multi-size ICO with standard uncompressed Windows BMP frames
    ico_path = os.path.join(assets_dir, "icon.ico")
    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=icon_sizes, bitmap_format="bmp")

    print(f"Saved icon to: {ico_path} and {png_path}")
    return ico_path


if __name__ == "__main__":
    generate_app_icon()
