from PIL import Image, ImageDraw, ImageFont

def apply_grid_overlay(image_path, output_path, step=75):
    """
    Applies a grid overlay with labeled coordinates to an image.

    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the image with the grid overlay.
        step (int): The step size for both vertical and horizontal grid lines (in pixels).
    """
    # Open and make a copy of the image to avoid modifying the original
    img = Image.open(image_path)
    overlay_img = img.copy()
    draw = ImageDraw.Draw(overlay_img)
    width, height = img.size

    # Load a font for the labels
    try:
        font = ImageFont.truetype("arial.ttf", 30)  # Smaller font for denser grid
    except IOError:
        font = ImageFont.load_default()

    # Draw vertical grid lines and X-axis labels
    for i, x in enumerate(range(0, width, step)):
        # Alternate between red and white for better visibility
        line_color = "white" if i % 2 == 0 else "red"
        draw.line((x, 0, x, height), fill=line_color, width=1)
        if x % 75 == 0:  # Show labels every 75 pixels
            draw.text((x + 2, 2), f"{x}", fill=line_color, font=font)

    # Draw horizontal grid lines and Y-axis labels
    for i, y in enumerate(range(0, height, step)):
        # Alternate between red and white for better visibility
        line_color = "white" if i % 2 == 0 else "red"
        draw.line((0, y, width, y), fill=line_color, width=1)
        if y % 75 == 0:  # Show labels every 75 pixels
            draw.text((2, y + 2), f"{y}", fill=line_color, font=font)

    # Save the modified image
    overlay_img.save(output_path)
    img.close()  # Close the original image