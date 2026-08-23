import os
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

def create_og_image(output_path):
    width = 1200
    height = 630
    
    # Background (Dark brand color #0A0A0B)
    img = Image.new('RGB', (width, height), color=(10, 10, 11))
    draw = ImageDraw.Draw(img)
    
    # Draw some accent elements (Purple #8B5CF6)
    draw.rectangle([0, 0, width, 10], fill=(139, 92, 246))
    draw.rectangle([0, height-10, width, height], fill=(139, 92, 246))
    
    # Load fonts if available, otherwise default
    try:
        # Try to use a system sans-serif font
        font_title = ImageFont.truetype("arialbd.ttf", 80)
        font_subtitle = ImageFont.truetype("arial.ttf", 40)
        font_dbs = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_dbs = ImageFont.load_default()

    # Draw Text
    title_text = "Fluxline"
    # Using textbbox instead of textsize which is deprecated in newer PIL
    try:
        title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
        title_width = title_bbox[2] - title_bbox[0]
    except AttributeError:
        title_width = draw.textlength(title_text, font=font_title)
        
    draw.text(((width - title_width) / 2, 120), title_text, font=font_title, fill=(250, 250, 250))
    
    subtitle_text = "Deterministic Database Migration"
    try:
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=font_subtitle)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    except AttributeError:
        subtitle_width = draw.textlength(subtitle_text, font=font_subtitle)
        
    draw.text(((width - subtitle_width) / 2, 240), subtitle_text, font=font_subtitle, fill=(139, 92, 246))

    dbs_text = "MSSQL   |   MySQL   |   PostgreSQL   |   Oracle"
    try:
        dbs_bbox = draw.textbbox((0, 0), dbs_text, font=font_dbs)
        dbs_width = dbs_bbox[2] - dbs_bbox[0]
    except AttributeError:
        dbs_width = draw.textlength(dbs_text, font=font_dbs)
        
    draw.text(((width - dbs_width) / 2, 450), dbs_text, font=font_dbs, fill=(160, 160, 170))
    
    # Save image
    img.save(output_path)
    print(f"Created {output_path}")

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "frontend", "public", "og-image.png")
    create_og_image(output_path)
