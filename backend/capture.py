"""Screenshot capture service for MineContext-v2."""

import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import mss
from loguru import logger

from backend.config import settings
from backend.database import db
from backend.models import ScreenshotCreate
from backend.utils.image_utils import (
    calculate_perceptual_hash,
    are_images_similar,
    compress_image,
    ensure_screenshot_dir,
    generate_screenshot_filename,
    get_file_size,
    cleanup_screenshots,
)


class CaptureService:
    """Screenshot capture service with background threading."""

    def __init__(self):
        """Initialize capture service."""
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.screenshots_captured = 0
        self.last_capture_time: Optional[datetime] = None
        self.last_hash: Optional[str] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the screenshot capture service."""
        if self.is_running:
            logger.warning("Capture service is already running")
            return

        logger.info("Starting screenshot capture service")
        if settings.capture.random_interval:
            logger.info(
                f"Random interval mode: {settings.capture.min_interval_seconds}-"
                f"{settings.capture.max_interval_seconds} seconds"
            )
        else:
            logger.info(f"Fixed interval mode: {settings.capture.interval_seconds} seconds")

        self.is_running = True
        self._stop_event.clear()

        # Start capture in background thread
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

    def stop(self):
        """Stop the screenshot capture service."""
        if not self.is_running:
            logger.warning("Capture service is not running")
            return

        logger.info("Stopping screenshot capture service")
        self.is_running = False
        self._stop_event.set()

        # Wait for thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)

    def get_status(self) -> dict:
        """Get current capture service status.

        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "interval_seconds": settings.capture.interval_seconds,
            "screenshots_captured": self.screenshots_captured,
            "last_capture_time": self.last_capture_time,
        }

    def _capture_loop(self):
        """Main capture loop running in background thread."""
        if settings.capture.random_interval:
            logger.info(
                f"Capture loop started with random interval "
                f"({settings.capture.min_interval_seconds}-{settings.capture.max_interval_seconds}s)"
            )
        else:
            logger.info(
                f"Capture loop started with {settings.capture.interval_seconds}s interval"
            )

        while not self._stop_event.is_set():
            try:
                self._capture_screenshot()
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")

            # Calculate next interval
            if settings.capture.random_interval:
                # Random interval between min and max
                next_interval = random.randint(
                    settings.capture.min_interval_seconds,
                    settings.capture.max_interval_seconds
                )
                logger.debug(f"Next capture in {next_interval} seconds")
            else:
                next_interval = settings.capture.interval_seconds

            # Wait for the interval or until stop event
            self._stop_event.wait(timeout=next_interval)

        logger.info("Capture loop stopped")

    def _capture_screenshot(self):
        """Capture a single screenshot and save to database."""
        try:
            # Ensure screenshot directory exists
            screenshot_dir = ensure_screenshot_dir()

            # Generate filename
            filename = generate_screenshot_filename()
            filepath = screenshot_dir / filename

            # Capture screenshot using mss
            with mss.mss() as sct:
                # Capture primary monitor (index 1)
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # Save screenshot
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))

            # Compress if enabled
            if settings.storage.compression:
                compress_image(str(filepath), quality=settings.storage.quality)

            # Calculate perceptual hash
            image_hash = calculate_perceptual_hash(str(filepath))

            # Check for duplicates if enabled
            if settings.capture.deduplicate and self.last_hash:
                if are_images_similar(image_hash, self.last_hash):
                    logger.debug(f"Skipping duplicate screenshot: {filename}")
                    filepath.unlink()  # Delete the duplicate
                    return

            # Also check database for duplicates
            if settings.capture.deduplicate and image_hash:
                existing = db.find_duplicate_hash(image_hash)
                if existing:
                    logger.debug(
                        f"Screenshot {filename} is duplicate of ID {existing.id}"
                    )
                    filepath.unlink()  # Delete the duplicate
                    return

            # Get file size
            file_size = get_file_size(str(filepath))

            # Create database record
            screenshot_data = ScreenshotCreate(
                filepath=str(filepath),
                image_hash=image_hash,
                file_size=file_size,
            )
            screenshot = db.create_screenshot(screenshot_data)

            # Update service state
            self.screenshots_captured += 1
            self.last_capture_time = datetime.now()
            self.last_hash = image_hash

            logger.info(
                f"Screenshot captured: {filename} (ID: {screenshot.id}, Size: {file_size} bytes)"
            )

            # Trigger TODO activity matching (async, non-blocking)
            try:
                from todolist.backend.services.activity_matcher import trigger_async_match
                trigger_async_match(screenshot.id)
            except ImportError:
                pass  # TodoList module not installed

            # Cleanup old screenshots if needed
            total_screenshots = db.get_total_screenshots()
            if total_screenshots > settings.capture.max_screenshots:
                deleted_db = db.cleanup_old_screenshots(settings.capture.max_screenshots)
                deleted_files = cleanup_screenshots(settings.capture.max_screenshots)
                logger.info(
                    f"Cleanup: {deleted_db} DB records, {deleted_files} files deleted"
                )

        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")

    def capture_now(self) -> Optional[int]:
        """Capture a screenshot immediately (manual capture).

        Returns:
            Screenshot ID if successful, None otherwise
        """
        try:
            # Ensure screenshot directory exists
            screenshot_dir = ensure_screenshot_dir()

            # Generate filename
            filename = generate_screenshot_filename()
            filepath = screenshot_dir / filename

            # Capture screenshot using mss
            with mss.mss() as sct:
                # Capture primary monitor (index 1)
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)

                # Save screenshot
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(filepath))

            # Compress if enabled
            if settings.storage.compression:
                compress_image(str(filepath), quality=settings.storage.quality)

            # Calculate perceptual hash
            image_hash = calculate_perceptual_hash(str(filepath))

            # Get file size
            file_size = get_file_size(str(filepath))

            # Create database record
            screenshot_data = ScreenshotCreate(
                filepath=str(filepath),
                image_hash=image_hash,
                file_size=file_size,
            )
            screenshot = db.create_screenshot(screenshot_data)

            logger.info(f"Manual screenshot captured: {filename} (ID: {screenshot.id})")

            # Trigger TODO activity matching (async, non-blocking)
            try:
                from todolist.backend.services.activity_matcher import trigger_async_match
                trigger_async_match(screenshot.id)
            except ImportError:
                pass  # TodoList module not installed

            return screenshot.id

        except Exception as e:
            logger.error(f"Error in manual capture: {e}")
            return None


# Global capture service instance
capture_service = CaptureService()
