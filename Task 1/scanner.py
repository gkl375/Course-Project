"""
scanner.py - Barcode / ISBN scanning via webcam (continuous mode for POS).
"""

import sys
import time
from typing import Callable, Optional

import cv2
import numpy as np
from pyzbar import pyzbar

# Must match every cv2.imshow / namedWindow title for this scanner UI.
SCANNER_WINDOW_TITLE = "Barcode Scanner"


def opencv_scanner_window_closed(title: str = SCANNER_WINDOW_TITLE) -> bool:
    """True if the HighGUI window was closed (e.g. user clicked X)."""
    try:
        return cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1
    except Exception:
        return True


def _open_video_capture(index: int = 0) -> cv2.VideoCapture:
    """
    Open default camera. On Windows, DirectShow (CAP_DSHOW) usually connects
    much faster than the default MSMF backend (often several seconds).
    """
    if sys.platform == "win32":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            return cap
        cap.release()
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
    return cap


def _show_scanner_splash(title: str = SCANNER_WINDOW_TITLE) -> None:
    """Show OpenCV window immediately so the UI does not feel frozen during warm-up."""
    h, w = 480, 640
    splash = np.zeros((h, w, 3), dtype=np.uint8)
    msg = "Opening camera..."
    cv2.putText(
        splash,
        msg,
        (120, h // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
    )
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.imshow(title, splash)
    cv2.waitKey(1)


def refocus_barcode_scanner_window(title: str = SCANNER_WINDOW_TITLE) -> None:
    """
    Bring the OpenCV scanner window back after a Tk messagebox steals focus
    (common on Windows).
    """
    try:
        cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(1)
        cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 0)
        cv2.waitKey(1)
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd:
                SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


class BarcodeScanner:
    """Handle barcode/ISBN validation and webcam scanning (GUI uses continuous mode)."""

    @staticmethod
    def validate_barcode(barcode_data: str) -> Optional[str]:
        """
        Validate and extract ISBN from barcode data.
        
        Args:
            barcode_data: Raw data from barcode
        
        Returns:
            ISBN-13 string or None
        """
        # Clean data
        isbn = barcode_data.strip()
        
        # Support both ISBN-13 and ISBN-10
        if len(isbn) == 13 and isbn.isdigit():
            return isbn
        elif len(isbn) == 10 and isbn.isdigit():
            # Convert ISBN-10 to ISBN-13 (simplified)
            return f"978{isbn[:9]}"
        
        return None

    @staticmethod
    def scan_webcam_continuous(
        on_valid_isbn: Callable[[str], None],
        *,
        timeout_ms: int = 0,
        min_seconds_same_isbn_absent: float = 1.25,
    ) -> bool:
        """
        Keep the webcam open and call *on_valid_isbn* for each new sighting.

        The same ISBN is only reported again after the decoder has **not** seen
        that ISBN for *min_seconds_same_isbn_absent* seconds. Brief dropouts
        while the code is still partly in frame no longer clear the latch (unlike
        a short frame counter). Move the barcode away until it stops reading, then
        show it again to add the same item again.

        Press ESC or close the window to exit. ``timeout_ms`` 0 = no time limit.
        Returns False if the camera could not be opened.
        """
        latched_isbn: Optional[str] = None
        last_latched_visible_at: Optional[float] = None

        try:
            cap = _open_video_capture(0)
            if not cap.isOpened():
                print("Error: Cannot open webcam")
                return False

            _show_scanner_splash(SCANNER_WINDOW_TITLE)
            print(
                "[Scanner] Continuous mode: ESC or close window to exit; "
                "move barcode out of view before re-scan same code."
            )

            start_time = cv2.getTickCount()
            fps = cv2.getTickFrequency()

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                barcodes = pyzbar.decode(frame)
                visible_valid: list[str] = []
                for barcode in barcodes:
                    barcode_data = barcode.data.decode("utf-8")
                    isbn = BarcodeScanner.validate_barcode(barcode_data)
                    (x, y, w, h) = barcode.rect
                    if isbn:
                        visible_valid.append(isbn)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 165, 255), 2)

                visible_set = set(visible_valid)
                now = time.monotonic()

                if latched_isbn is not None:
                    if latched_isbn in visible_set:
                        last_latched_visible_at = now
                    elif (
                        last_latched_visible_at is not None
                        and now - last_latched_visible_at >= min_seconds_same_isbn_absent
                    ):
                        latched_isbn = None
                        last_latched_visible_at = None

                if visible_set:
                    if latched_isbn is not None and latched_isbn in visible_set:
                        pass
                    else:
                        for isbn in visible_valid:
                            on_valid_isbn(isbn)
                            latched_isbn = isbn
                            last_latched_visible_at = now
                            print(f"[Scanner] Detected (cart): {isbn}")
                            break

                cv2.putText(
                    frame,
                    f"No read {min_seconds_same_isbn_absent:.1f}s -> same ISBN ok again",
                    (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESC to close",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow(SCANNER_WINDOW_TITLE, frame)

                if timeout_ms > 0:
                    elapsed = (cv2.getTickCount() - start_time) / fps
                    if elapsed * 1000 > timeout_ms:
                        print("[Scanner] Timeout - webcam closed")
                        break

                key = cv2.waitKey(1) & 0xFF
                if opencv_scanner_window_closed():
                    print("[Scanner] Window closed")
                    break
                if key == 27:
                    print("[Scanner] Closed (ESC)")
                    break

            cap.release()
            cv2.destroyAllWindows()
            return True

        except Exception as e:
            print(f"[Scanner] Error: {e}")
            return False
