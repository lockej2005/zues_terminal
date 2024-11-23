from PIL import Image, ImageDraw, ImageFont

def apply_grid_overlay(image_path, output_path, step=500):
    """
    Applies a grid overlay with labeled coordinates to an image.

    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the image with the grid overlay.
        step (int): The step size for both vertical and horizontal grid lines (in pixels).
    """
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Load a font for the labels (uses a default PIL font or fallback)
    try:
        font = ImageFont.truetype("arial.ttf", 72)
    except IOError:
        font = ImageFont.load_default()

    # Draw vertical grid lines and X-axis labels
    for x in range(0, width, step):
        draw.line((x, 0, x, height), fill="gray", width=2)
        draw.text((x + 5, 5), f"{x}", fill="white", font=font)

    # Draw horizontal grid lines and Y-axis labels
    for y in range(0, height, step):
        draw.line((0, y, width, y), fill="gray", width=2)
        draw.text((5, y + 5), f"{y}", fill="white", font=font)

    # Save the modified image
    img.save(output_path)
