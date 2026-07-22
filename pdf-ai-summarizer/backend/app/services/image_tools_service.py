import io

from fastapi import HTTPException
from PIL import Image

EXT_TO_PIL_FORMAT = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
}


def convert_image(file_bytes: bytes, original_ext: str, target_format: str, quality: int) -> tuple[bytes, str]:
    try:
        image = Image.open(io.BytesIO(file_bytes))

        if target_format == "same":
            save_format = EXT_TO_PIL_FORMAT.get(original_ext.lower(), image.format or "PNG")
        else:
            save_format = EXT_TO_PIL_FORMAT.get(target_format.lower(), target_format.upper())

        if save_format == "JPEG" and image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")

        output = io.BytesIO()
        save_kwargs: dict = {"optimize": True}
        if save_format in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
        image.save(output, format=save_format, **save_kwargs)

        out_ext = "jpg" if save_format == "JPEG" else save_format.lower()
        return output.getvalue(), out_ext
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Cannot process image file") from exc
