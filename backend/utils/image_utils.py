"""Image processing utilities for MineContext-v2."""

import os
from pathlib import Path
from typing import Optional, Tuple

import imagehash
from PIL import Image
from loguru import logger

from backend.config import settings


def calculate_perceptual_hash(image_path: str) -> str:
    """Calculate perceptual hash of an image.

    Args:
        image_path: Path to the image file

    Returns:
        Hexadecimal string representation of the perceptual hash
    """
    try:
        with Image.open(image_path) as img:
            # Use average hash for faster computation
            hash_value = imagehash.average_hash(img)
            return str(hash_value)
    except Exception as e:
        logger.error(f"Error calculating hash for {image_path}: {e}")
        return ""


def calculate_hash_difference(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two perceptual hashes.

    Args:
        hash1: First hash string
        hash2: Second hash string

    Returns:
        Hamming distance (number of different bits)
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return h1 - h2
    except Exception as e:
        logger.error(f"Error calculating hash difference: {e}")
        return 999  # Return large number on error


def are_images_similar(hash1: str, hash2: str, threshold: Optional[int] = None) -> bool:
    """Check if two images are similar based on their hashes.

    Args:
        hash1: First image hash
        hash2: Second image hash
        threshold: Maximum hash difference to consider similar (default from config)

    Returns:
        True if images are similar, False otherwise
    """
    if not hash1 or not hash2:
        return False

    threshold = threshold or settings.capture.hash_threshold
    difference = calculate_hash_difference(hash1, hash2)
    return difference <= threshold


def compress_image(
    input_path: str,
    output_path: Optional[str] = None,
    quality: Optional[int] = None,
    max_size: Optional[Tuple[int, int]] = None,
) -> str:
    """Compress an image to reduce file size.

    Args:
        input_path: Path to input image
        output_path: Path to save compressed image (default: overwrite input)
        quality: JPEG quality (1-100, default from config)
        max_size: Maximum dimensions (width, height). If provided, image will be resized.

    Returns:
        Path to compressed image
    """
    output_path = output_path or input_path
    quality = quality or settings.storage.quality

    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize if max_size is specified
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save with compression
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            logger.debug(f"Compressed image saved to {output_path}")

    except Exception as e:
        logger.error(f"Error compressing image {input_path}: {e}")
        # If compression fails, just copy the original
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)

    return output_path


def get_image_size(image_path: str) -> Tuple[int, int]:
    """Get image dimensions.

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (width, height)
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image size for {image_path}: {e}")
        return (0, 0)


def get_file_size(file_path: str) -> int:
    """Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0


def ensure_screenshot_dir() -> Path:
    """Ensure screenshot directory exists.

    Returns:
        Path object for screenshot directory
    """
    screenshot_dir = Path(settings.capture.screenshot_dir)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    return screenshot_dir


def generate_screenshot_filename() -> str:
    """Generate a unique filename for a screenshot.

    Returns:
        Filename in format: screenshot_YYYYMMDD_HHMMSS_microseconds.jpg
    """
    from datetime import datetime

    timestamp = datetime.now()
    filename = timestamp.strftime("screenshot_%Y%m%d_%H%M%S_%f.jpg")
    return filename


def cleanup_screenshots(keep_count: int) -> int:
    """Delete oldest screenshot files.

    Args:
        keep_count: Number of most recent screenshots to keep

    Returns:
        Number of files deleted
    """
    screenshot_dir = Path(settings.capture.screenshot_dir)

    if not screenshot_dir.exists():
        return 0

    # Get all screenshot files sorted by modification time
    screenshot_files = sorted(
        screenshot_dir.glob("screenshot_*.jpg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Delete files beyond keep_count
    deleted_count = 0
    for file_path in screenshot_files[keep_count:]:
        try:
            file_path.unlink()
            deleted_count += 1
            logger.debug(f"Deleted old screenshot: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old screenshot files")

    return deleted_count
