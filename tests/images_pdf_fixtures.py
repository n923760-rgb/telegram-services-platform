from io import BytesIO

from PIL import Image, ImageDraw


def picture(width=120, height=240, *, color="red", orientation=None, transparent=False):
    mode = "RGBA" if transparent else "RGB"
    background = (0, 0, 0, 0) if transparent else color
    with Image.new(mode, (width, height), background) as image:
        draw = ImageDraw.Draw(image)
        draw.rectangle((width // 4, height // 4, 3 * width // 4, 3 * height // 4), fill=color)
        draw.text((width // 3, height // 3), "00123", fill="black")
        output = BytesIO()
        if orientation is not None:
            exif = Image.Exif()
            exif[274] = orientation
            exif[270] = "Synthetic private metadata must not survive"
            image.save(output, format="PNG", exif=exif)
        else:
            image.save(output, format="PNG")
        return output.getvalue()
