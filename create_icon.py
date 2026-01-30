"""
Generate NIBOR Recon app icon - High Quality Version
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

def create_icon():
    # Create at 4x size for better quality, then downscale
    base_size = 512

    # Colors - Swedbank/fintech theme
    BG_DARK = "#0B1220"
    CARD_BG = "#141E30"
    ORANGE = "#FF6B35"
    ORANGE_GLOW = "#FF8A5C"
    GREEN = "#22C55E"

    # Create high-res image
    img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    margin = 20
    corner_radius = 80

    # Outer glow effect - draw multiple expanding rectangles with decreasing opacity
    for i in range(15, 0, -1):
        glow_alpha = int(20 * (15 - i) / 15)
        glow_color = (255, 107, 53, glow_alpha)
        glow_img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        glow_draw.rounded_rectangle(
            [margin - i*2, margin - i*2, base_size - margin + i*2, base_size - margin + i*2],
            radius=corner_radius + i,
            fill=glow_color
        )
        img = Image.alpha_composite(img, glow_img)

    draw = ImageDraw.Draw(img)

    # Main card background
    draw.rounded_rectangle(
        [margin, margin, base_size - margin, base_size - margin],
        radius=corner_radius,
        fill=CARD_BG
    )

    # Orange border
    draw.rounded_rectangle(
        [margin, margin, base_size - margin, base_size - margin],
        radius=corner_radius,
        fill=None,
        outline=ORANGE,
        width=8
    )

    # Inner subtle border
    draw.rounded_rectangle(
        [margin + 12, margin + 12, base_size - margin - 12, base_size - margin - 12],
        radius=corner_radius - 10,
        fill=None,
        outline="#1E2D45",
        width=2
    )

    # Load a proper font for the "N"
    font_size = 280
    try:
        # Try different fonts
        for font_name in ["arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except:
                continue
        else:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Calculate text position
    letter = "N"
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (base_size - text_width) // 2 - 20
    y = (base_size - text_height) // 2 - 50

    # Draw text shadow/glow
    shadow_img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_draw.text((x, y), letter, font=font, fill=(0, 0, 0, 150))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.alpha_composite(img, shadow_img)

    # Draw orange glow behind text
    glow_img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.text((x, y), letter, font=font, fill=(255, 107, 53, 100))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=15))
    img = Image.alpha_composite(img, glow_img)

    # Draw main "N" text
    draw = ImageDraw.Draw(img)
    draw.text((x, y), letter, font=font, fill=ORANGE)

    # Draw checkmark
    check_font_size = 140
    try:
        check_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", check_font_size)
    except:
        check_font = font

    # Position checkmark in bottom right
    check_x = base_size - 160
    check_y = base_size - 200

    # Draw green glow for checkmark
    check_glow = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    check_glow_draw = ImageDraw.Draw(check_glow)
    check_glow_draw.text((check_x, check_y), "✓", font=check_font, fill=(34, 197, 94, 120))
    check_glow = check_glow.filter(ImageFilter.GaussianBlur(radius=10))
    img = Image.alpha_composite(img, check_glow)

    # Draw checkmark
    draw = ImageDraw.Draw(img)
    draw.text((check_x, check_y), "✓", font=check_font, fill=GREEN)

    # Save high-res PNG preview
    png_path = os.path.join(os.path.dirname(__file__), "assets", "icon_preview.png")
    img.save(png_path, format='PNG')
    print(f"Preview saved: {png_path}")

    # Create ICO with multiple sizes (downscaled from high-res)
    ico_sizes = [256, 128, 64, 48, 32, 16]
    ico_images = []

    for size in ico_sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        ico_images.append(resized)

    # Save as .ico
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    ico_images[0].save(
        icon_path,
        format='ICO',
        sizes=[(s, s) for s in ico_sizes],
        append_images=ico_images[1:]
    )
    print(f"Icon created: {icon_path}")

    return icon_path

if __name__ == "__main__":
    create_icon()
