"""Generate local responsive WebP variants. Requires Pillow; originals stay intact."""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
for folder in ('products', 'people', 'shop'):
    output = ROOT / 'images' / folder / 'responsive'
    output.mkdir(exist_ok=True)
    for source in (ROOT / 'images' / folder).glob('*.webp'):
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original)
            for width in (480, 800):
                if width < image.width:
                    height = round(image.height * width / image.width)
                    image.resize((width, height), Image.Resampling.LANCZOS).save(
                        output / f'{source.stem}-{width}.webp', 'WEBP', quality=82,
                    )
