"""
Generate NIBOR Recon app icon
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Icon sizes for .ico file
    sizes = [256, 128, 64, 48, 32, 16]

    # Colors - Swedbank/fintech theme
    BG_DARK = "#0B1220"
    ORANGE = "#FF6B35"
    ORANGE_LIGHT = "#FF8A5C"
    WHITE = "#FFFFFF"

    images = []

    for size in sizes:
        # Create image with dark background
        img = Image.new('RGBA', (size, size), BG_DARK)
        draw = ImageDraw.Draw(img)

        # Draw rounded rectangle background
        padding = size // 10
        corner_radius = size // 5

        # Draw orange accent circle/glow in background
        glow_size = int(size * 0.7)
        glow_pos = (size - glow_size) // 2

        # Main card background with subtle border
        card_margin = size // 16
        draw.rounded_rectangle(
            [card_margin, card_margin, size - card_margin, size - card_margin],
            radius=corner_radius,
            fill="#121C2E",
            outline=ORANGE,
            width=max(1, size // 32)
        )

        # Draw "N" letter
        try:
            # Try to use a nice font
            font_size = int(size * 0.45)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()

        # Draw the "N" with orange color
        letter = "N"
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 10

        # Draw text shadow
        shadow_offset = max(1, size // 64)
        draw.text((x + shadow_offset, y + shadow_offset), letter, font=font, fill="#000000")

        # Draw main text
        draw.text((x, y), letter, font=font, fill=ORANGE)

        # Draw checkmark for "Recon" (verification)
        check_size = size // 4
        check_x = size // 2 + size // 8
        check_y = size // 2 + size // 8

        # Checkmark path
        check_width = max(2, size // 20)

        # Draw checkmark
        points = [
            (check_x - check_size//3, check_y),
            (check_x - check_size//10, check_y + check_size//4),
            (check_x + check_size//3, check_y - check_size//4)
        ]
        draw.line(points[:2], fill="#22C55E", width=check_width)
        draw.line(points[1:], fill="#22C55E", width=check_width)

        images.append(img)

    # Save as .ico
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"Icon created: {icon_path}")

    # Also save a PNG preview
    png_path = os.path.join(os.path.dirname(__file__), "assets", "icon_preview.png")
    images[0].save(png_path, format='PNG')
    print(f"Preview saved: {png_path}")

    return icon_path

if __name__ == "__main__":
    create_icon()
