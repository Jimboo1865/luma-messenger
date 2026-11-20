from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from string import Template

import qrcodegen  # Vendored (Nayuki, MIT) — no pip install needed for {qr_code}

from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtCore import QPointF, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# ==============================================================================
# ==============================================================================
#  VISUAL THEME & STYLING (Edit colors, padding, and radii here)
#  Two palettes — light and dark — following the macOS system appearance.
#  Checkboxes intentionally use the native macOS rendering (no custom indicator rules), so they draw as proper Aqua checkboxes with a tick
#  instead of solid squares.
# ==============================================================================
LIGHT_PALETTE = {
    "bg": "#F5F5F7", "sidebar_bg": "#EBEBEF", "card": "#FFFFFF",
    "text": "#1D1D1F", "muted": "#6E6E73",
    "accent": "#007AFF", "accent_hover": "#0066D6", "accent_border": "#0066D6",
    "accent_disabled": "#A6CFFF",
    "card_border": "#E4E4E9", "sidebar_border": "#D5D5DC",
    "btn_bg": "#FFFFFF", "btn_border": "#CECED6", "btn_hover_bg": "#F2F2F7",
    "btn_hover_border": "#B8B8C2", "btn_pressed_bg": "#E5E5EA",
    "chip_bg": "#EEF5FF", "chip_border": "#C6DFFF", "chip_text": "#005EC4",
    "chip_hover": "#DCEBFF",
    "input_bg": "#FFFFFF", "input_border": "#D2D2D7",
    "combo_hover_bg": "#FAFAFC", "combo_hover_border": "#B4B4BE",
    "list_hover": "#DFDFE6",
    "table_alt": "#FAFAFC", "table_border": "#ECECF0", "table_grid": "#F0F0F4",
    "table_header_bg": "#F7F7FA", "table_header_border": "#E2E2E8",
    "selection_bg": "#E3F0FF", "selection_text": "#1D1D1F",
}

DARK_PALETTE = {
    "bg": "#1C1C1E", "sidebar_bg": "#232326", "card": "#2C2C2E",
    "text": "#F5F5F7", "muted": "#98989D",
    "accent": "#0A84FF", "accent_hover": "#409CFF", "accent_border": "#0A84FF",
    "accent_disabled": "#2E4A66",
    "card_border": "#38383A", "sidebar_border": "#38383A",
    "btn_bg": "#2C2C2E", "btn_border": "#48484A", "btn_hover_bg": "#3A3A3C",
    "btn_hover_border": "#636366", "btn_pressed_bg": "#48484A",
    "chip_bg": "#12283D", "chip_border": "#1F4E79", "chip_text": "#7AB8FF",
    "chip_hover": "#1B3A5C",
    "input_bg": "#1C1C1E", "input_border": "#48484A",
    "combo_hover_bg": "#2C2C2E", "combo_hover_border": "#636366",
    "list_hover": "#3A3A3C",
    "table_alt": "#232326", "table_border": "#38383A", "table_grid": "#2C2C2E",
    "table_header_bg": "#232326", "table_header_border": "#38383A",
    "selection_bg": "#0A2A4A", "selection_text": "#F5F5F7",
}

QSS_TEMPLATE = """
QMainWindow, QWidget#CentralBg {
    background-color: $bg;
    color: $text;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QWidget {
    color: $text;
}
QFrame#Card {
    background-color: $card;
    border: 1px solid $card_border;
    border-radius: 14px;
}
QFrame#Sidebar {
    background-color: $sidebar_bg;
    border-right: 1px solid $sidebar_border;
}
QLabel#TitleLabel {
    font-size: 16px;
    font-weight: 700;
    color: $text;
    background: transparent;
}
QLabel#AppTitle {
    font-size: 20px;
    font-weight: 700;
    color: $text;
    background: transparent;
}
QLabel#SubtitleLabel {
    font-size: 11px;
    color: $muted;
    background: transparent;
}
QLabel#SectionHeader {
    font-size: 11px;
    font-weight: 700;
    color: $muted;
    letter-spacing: 0.6px;
    background: transparent;
    margin-top: 4px;
}

/* --- Buttons --- */
QPushButton {
    background-color: $btn_bg;
    border: 1px solid $btn_border;
    border-radius: 8px;
    padding: 7px 13px;
    font-weight: 500;
    color: $text;
}
QPushButton:hover {
    background-color: $btn_hover_bg;
    border-color: $btn_hover_border;
}
QPushButton:pressed {
    background-color: $btn_pressed_bg;
}
QPushButton#PrimaryBtn {
    background-color: $accent;
    border: 1px solid $accent_border;
    color: #FFFFFF;
    font-weight: 600;
}
QPushButton#PrimaryBtn:hover {
    background-color: $accent_hover;
}
QPushButton#PrimaryBtn:disabled {
    background-color: $accent_disabled;
    border-color: $accent_disabled;
    color: #FFFFFF;
}
QPushButton#ChipBtn {
    background-color: $chip_bg;
    border: 1px solid $chip_border;
    color: $chip_text;
    border-radius: 11px;
    padding: 3px 10px;
    font-size: 11px;
    font-family: "SF Mono", Menlo, monospace;
}
QPushButton#ChipBtn:hover {
    background-color: $chip_hover;
}

/* --- Inputs & Modern Dropdowns --- */
QLineEdit {
    background-color: $input_bg;
    color: $text;
    border: 1px solid $input_border;
    border-radius: 8px;
    padding: 6px 10px;
}
QLineEdit:focus {
    border: 1.5px solid $accent;
}

QComboBox {
    background-color: $input_bg;
    color: $text;
    border: 1px solid $input_border;
    border-radius: 8px;
    padding: 6px 28px 6px 10px;
    font-weight: 500;
}
QComboBox:hover {
    background-color: $combo_hover_bg;
    border-color: $combo_hover_border;
}
QComboBox:focus, QComboBox:on {
    border: 1.5px solid $accent;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    background: transparent;
}
QComboBox QAbstractItemView {
    background-color: $card;
    color: $text;
    border: 1px solid $input_border;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: $accent;
    selection-color: #FFFFFF;
}
QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    border-radius: 5px;
    min-height: 22px;
}

/* --- Checkboxes: native macOS rendering (no custom indicator styling) --- */
QCheckBox {
    spacing: 8px;
    color: $text;
    background: transparent;
}

/* --- Sidebar Cohort List --- */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    color: $text;
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 3px;
}
QListWidget::item:hover {
    background-color: $list_hover;
}
QListWidget::item:selected {
    background-color: $accent;
    color: #FFFFFF;
    font-weight: 600;
}

/* --- Guest Roster Table --- */
QTableWidget {
    background-color: $card;
    color: $text;
    alternate-background-color: $table_alt;
    border: 1px solid $table_border;
    border-radius: 8px;
    gridline-color: $table_grid;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
    color: $text;
}
QHeaderView::section {
    background-color: $table_header_bg;
    border: none;
    border-bottom: 1px solid $table_header_border;
    padding: 7px 8px;
    font-weight: 700;
    color: $muted;
    font-size: 11px;
}

/* --- Message Composer & Preview --- */
QTextEdit {
    background-color: $input_bg;
    color: $text;
    border: 1px solid $btn_border;
    border-radius: 8px;
    padding: 9px;
    font-size: 13px;
}
QTextEdit:focus {
    background-color: $card;
    border: 1.5px solid $accent;
}
QFrame#PreviewBubble {
    background-color: $accent;
    border-radius: 15px;
    padding: 10px 14px;
}
QLabel#PreviewText {
    color: #FFFFFF;
    font-size: 13px;
    background: transparent;
}
"""

def build_qss(palette):
    """Render the Apple-style stylesheet from a light/dark palette."""
    return Template(QSS_TEMPLATE).substitute(palette)

# Backwards-compatible default; the entry point picks light/dark at launch.
APP_QSS = build_qss(LIGHT_PALETTE)

CORE_COLS = {
    "guest_id", "name", "first_name", "last_name", "email", "phone_number",
    "created_at", "approval_status", "checked_in_at", "qr_code_url",
    "ticket_type_id", "ticket_name",
}
NOISE_PREFIXES = ("utm_", "amount", "survey_")
NOISE_EXACT = {
    "google_click_id", "meta_click_id", "x_click_id", "linkedin_click_id",
    "tiktok_click_id", "reddit_click_id", "yandex_click_id", "referrer",
    "referred_by", "currency", "coupon_code", "eth_address", "solana_address",
}

QR_TAG_RE = re.compile(r"\{qr_code(?::([A-Za-z0-9_]+))?\}")


def _qr_cache_dir() -> Path:
    """QR images must live where Messages.app can read them (~/Pictures).

    The app is sandboxed: attachments staged in /tmp or ~/Desktop silently
    fail to deliver, so QR PNGs are cached under ~/Pictures instead.
    """
    d = Path.home() / "Pictures" / "Luma Messenger" / "QR Codes"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_qr_png(qr: "qrcodegen.QrCode", out: Path, box_size: int = 20, border: int = 2) -> None:
    """Write a QR code as a PNG using only the standard library.

    RGB, 8-bit per channel; each scanline starts with a filter-type 0 byte.
    No Pillow or Qt needed.
    """
    import struct
    import zlib

    def chunk(ctype: bytes, data: bytes) -> bytes:
        body = ctype + data
        return (
            struct.pack(">I", len(data))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    n = qr.get_size()
    side = n + border * 2
    px = side * box_size
    ihdr = struct.pack(">IIBBBBB", px, px, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for my in range(side):
        row = bytearray()
        for mx in range(side):
            gx, gy = mx - border, my - border
            dark = 0 <= gx < n and 0 <= gy < n and qr.get_module(gx, gy)
            row.extend((b"\x00\x00\x00" if dark else b"\xff\xff\xff") * box_size)
        for _ in range(box_size):
            raw.append(0)
            raw.extend(row)
    out.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def _qr_png_for_url(url: str) -> Path:
    """Render a standard QR PNG for a URL, cached by URL hash.

    delphi.tools qr-genny has no server API to call (it renders client-side
    in the browser), so the code is rendered locally with the vendored
    qrcodegen library — same QR standard, error-correction level M (15%) —
    and it scans identically. No pip install needed in any Python.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    out = _qr_cache_dir() / f"qr-{digest}.png"
    if not out.exists():
        qr = qrcodegen.QrCode.encode_text(url, qrcodegen.QrCode.Ecc.MEDIUM)
        _write_qr_png(qr, out)
    return out


def _qr_jpg_for_url(url: str) -> Path:
    """JPEG version of the guest's QR code — the file actually sent.

    A PNG sent via AppleScript arrives as a downloadable file instead of an
    inline image, so the QR goes out as a JPEG, which Messages always shows
    inline. The PNG stays cached as the master copy; falls back to it if
    the conversion ever fails.
    """
    png = _qr_png_for_url(url)
    jpg = png.with_suffix(".jpg")
    if not jpg.exists():
        img = QImage(str(png))
        if img.isNull():
            return png
        img = img.convertToFormat(QImage.Format_RGB888)
        if not img.save(str(jpg), "JPG", 95):
            return png
    return jpg


class MessageSenderWorker(QThread):
    progress = Signal(int, int, str, str)
    finished_batch = Signal(int, int)

    def __init__(self, queue_items: list[dict], dry_run: bool = False, qr_via_paste: bool = False):
        super().__init__()
        self.queue_items = queue_items
        self.dry_run = dry_run
        self.qr_via_paste = qr_via_paste
        self._cancelled = False
        self.paste_blocked_reason = None
        self._paste_probe_done = False

    def cancel(self):
        self._cancelled = True

    def _paste_available(self) -> bool:
        """Probe once: can this process drive System Events keystrokes?

        Without Accessibility permission the keystrokes silently do nothing
        (Messages still opens — only the paste/send never happen), so check
        up front and fail loudly instead of a batch of text-only messages
        that look like successes.
        """
        if self._paste_probe_done:
            return self.paste_blocked_reason is None
        self._paste_probe_done = True
        try:
            subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of first process'],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception:
            self.paste_blocked_reason = (
                "Accessibility permission missing — allow this app in "
                "System Settings → Privacy & Security → Accessibility, then retry."
            )
            return False
        return True

    def run(self):
        sent = 0
        failed = 0
        total = len(self.queue_items)

        # Routes via iMessage first; if recipient is Android/non-iMessage,
        # falls back to SMS/RCS forwarding via paired iPhone.
        applescript = """
        on run {targetPhone, targetMessage}
            tell application "Messages"
                try
                    set imService to 1st service whose service type = iMessage
                    send targetMessage to buddy targetPhone of imService
                on error
                    set smsService to 1st service whose service type = SMS
                    send targetMessage to buddy targetPhone of smsService
                end try
            end tell
        end run
        """

        # QR images only travel over iMessage (no SMS fallback for files).
        image_applescript = """
        on run {targetPhone, imagePath}
            tell application "Messages"
                set imService to 1st service whose service type = iMessage
                send POSIX file imagePath to buddy targetPhone of imService
            end tell
        end run
        """

        # Paste route: `send POSIX file` always creates a generic file
        # attachment, so a QR sent that way shows as a downloadable file,
        # not an inline photo. Pasting the image into the compose field
        # makes Messages treat it as an inline photo (the way a user
        # pasting a photo behaves). Costs: Messages comes to the front for
        # each QR, System Events keystrokes need Accessibility permission,
        # and the Mac is busy while a batch runs — don't touch it mid-send.
        paste_applescript = """
        on run {targetPhone, imagePath}
            set the clipboard to (read (POSIX file imagePath) as JPEG picture)
            -- Open the conversation directly instead of Cmd+N + typing the
            -- number: typing left focus stuck in the To field, so Cmd+V
            -- pasted into a text-only field and nothing happened. The sms:
            -- URL opens the thread with the message field focused.
            open location ("sms:" & targetPhone)
            delay 1.5
            tell application "Messages" to activate
            delay 0.5
            tell application "System Events"
                keystroke "v" using {command down}
                delay 1
                keystroke return
                delay 1
            end tell
        end run
        """

        for idx, item in enumerate(self.queue_items, start=1):
            if self._cancelled:
                break

            phone = item["phone"]
            body = item["message"]
            name = item["name"]

            if self.dry_run:
                time.sleep(0.2)
                sent += 1
                if item.get("qr_path"):
                    status = "Dry Run OK + QR (paste)" if self.qr_via_paste else "Dry Run OK + QR"
                elif item.get("qr_wanted"):
                    status = "Dry Run OK (no QR link)"
                else:
                    status = "Dry Run OK"
                self.progress.emit(idx, total, name, status)
                continue

            try:
                subprocess.run(
                    ["osascript", "-e", applescript, phone, body],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                failed += 1
                err_msg = (exc.stderr or "AppleScript error").strip()
                self.progress.emit(idx, total, name, f"Failed: {err_msg}")
            else:
                sent += 1
                status = "Sent"
                qr_path = item.get("qr_path")
                if item.get("qr_wanted") and qr_path:
                    if self.qr_via_paste and not self._paste_available():
                        status = "Sent (QR paste blocked: Accessibility permission)"
                    else:
                        qr_script = paste_applescript if self.qr_via_paste else image_applescript
                        try:
                            subprocess.run(
                                ["osascript", "-e", qr_script, phone, qr_path],
                                check=True,
                                capture_output=True,
                                text=True,
                            )
                            status = "Sent + QR (pasted)" if self.qr_via_paste else "Sent + QR"
                        except subprocess.CalledProcessError as exc:
                            err = (exc.stderr or "").strip()
                            how = "paste" if self.qr_via_paste else "send"
                            status = f"Sent (QR {how} failed: {err[:100]})" if err else f"Sent (QR {how} failed)"
                elif item.get("qr_wanted"):
                    status = "Sent (no QR link)"
                self.progress.emit(idx, total, name, status)

            if idx < total and not self._cancelled:
                time.sleep(random.uniform(5.0, 10.0))

        self.finished_batch.emit(sent, failed)


class DryRunPreviewDialog(QDialog):
    """Step through a dry-run batch: rendered message + QR image per guest.

    Nothing is sent from this dialog. "Send for Real" closes it and lets the
    caller start the live worker for the same queue (after a fresh confirm).
    """

    def __init__(self, queue_items: list[dict], parent=None):
        super().__init__(parent)
        self.queue_items = queue_items
        self.idx = 0
        self.send_real = False
        self.main_window = parent
        self.setWindowTitle("Dry Run Preview")
        self.resize(460, 660)

        muted = "#98989D" if (parent is not None and getattr(parent, "dark_mode", False)) else "#6E6E73"
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.lbl_counter = QLabel()
        self.lbl_counter.setStyleSheet(f"color: {muted}; font-size: 11px;")
        layout.addWidget(self.lbl_counter)

        self.lbl_recipient = QLabel()
        self.lbl_recipient.setWordWrap(True)
        layout.addWidget(self.lbl_recipient)

        bubble = QFrame(objectName="PreviewBubble")
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(4, 4, 4, 4)
        self.lbl_message = QLabel(objectName="PreviewText")
        self.lbl_message.setWordWrap(True)
        self.lbl_message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble_layout.addWidget(self.lbl_message)
        layout.addWidget(bubble)

        self.lbl_qr = QLabel()
        self.lbl_qr.setAlignment(Qt.AlignCenter)
        self.lbl_qr.setMinimumHeight(280)
        layout.addWidget(self.lbl_qr)
        self.lbl_qr_note = QLabel()
        self.lbl_qr_note.setAlignment(Qt.AlignCenter)
        self.lbl_qr_note.setWordWrap(True)
        layout.addWidget(self.lbl_qr_note)

        layout.addStretch()

        btn_row = QHBoxLayout()
        self.btn_prev = QPushButton("← Previous")
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next = QPushButton("Next →")
        self.btn_next.clicked.connect(self._next)
        self.btn_send_real = QPushButton("Send for Real", objectName="PrimaryBtn")
        self.btn_send_real.clicked.connect(self._on_send_real)
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_prev)
        btn_row.addWidget(self.btn_next)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_send_real)
        btn_row.addWidget(self.btn_close)
        layout.addLayout(btn_row)

        self._show(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self._prev()
        elif event.key() == Qt.Key_Right:
            self._next()
        else:
            super().keyPressEvent(event)

    def _prev(self):
        self._show(self.idx - 1)

    def _next(self):
        self._show(self.idx + 1)

    def _on_send_real(self):
        self.send_real = True
        self.accept()

    def _paste_qr_enabled(self) -> bool:
        mw = self.main_window
        chk = getattr(mw, "chk_paste_qr", None) if mw is not None else None
        return bool(chk is not None and chk.isChecked())

    def _show(self, idx: int):
        if not self.queue_items:
            return
        self.idx = max(0, min(idx, len(self.queue_items) - 1))
        item = self.queue_items[self.idx]
        total = len(self.queue_items)
        self.lbl_counter.setText(f"{self.idx + 1} of {total}")
        self.lbl_recipient.setText(f"To: {item['name']} ({item['phone']})")
        self.lbl_message.setText(item["message"] or "(empty message)")
        if item.get("qr_path"):
            pix = QPixmap(item["qr_path"])
            if pix.isNull():
                self.lbl_qr.clear()
                self.lbl_qr.setText("QR image could not be loaded")
                self.lbl_qr_note.setText(item["qr_path"])
            else:
                self.lbl_qr.setPixmap(
                    pix.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.lbl_qr_note.setText("QR code that will paste inline" if self._paste_qr_enabled() else "QR code that will attach")
        elif item.get("qr_wanted"):
            self.lbl_qr.clear()
            self.lbl_qr.setText("No QR link for this guest")
            self.lbl_qr_note.setText("This guest has no ticket link, so no image attaches.")
        else:
            self.lbl_qr.clear()
            self.lbl_qr.setText("No QR code in this message")
            self.lbl_qr_note.setText("Add {qr_code} to the template to attach each guest's ticket QR.")
        self.btn_prev.setEnabled(self.idx > 0)
        self.btn_next.setEnabled(self.idx < total - 1)
        if item.get("qr_path"):
            status = "Dry Run OK + QR (paste)" if self._paste_qr_enabled() else "Dry Run OK + QR"
        elif item.get("qr_wanted"):
            status = "Dry Run OK (no QR link)"
        else:
            status = "Dry Run OK"
        if self.main_window is not None and hasattr(self.main_window, "lbl_send_status"):
            self.main_window.lbl_send_status.setText(
                f"[Dry Run {self.idx + 1}/{total}] {item['name']}: {status}"
            )


class ModernComboBox(QComboBox):
    """QComboBox with a crisp Retina-rendered chevron instead of the 90s arrow."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#6E6E73"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        cx = self.width() - 16
        cy = self.height() / 2.0
        painter.drawPolyline([
            QPointF(cx - 4, cy - 2),
            QPointF(cx, cy + 2.5),
            QPointF(cx + 4, cy - 2),
        ])
        painter.end()


class LumaMessengerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Luma Event Messenger")
        self.resize(1260, 800)

        self.watch_dir = Path.home() / "Downloads"
        self.current_csv_path: Path | None = None
        self.rows: list[dict[str, str]] = []
        self.columns: list[str] = []

        # Persisted per-CSV state in .labels.json
        self.labels_map: dict[str, list[str]] = {}
        self.checked_map: dict[str, bool] = {}

        self.group_templates: dict[str, str] = {}
        self.active_cohort: str = "__ALL__"
        self.worker: MessageSenderWorker | None = None
        self.dark_mode = False

        self._build_ui()
        self._scan_folder(self.watch_dir)

    def _build_ui(self):
        root = QWidget(objectName="CentralBg")
        self.setCentralWidget(root)
        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Sidebar ---
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(250)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 18, 16, 18)
        sb_layout.setSpacing(10)

        sb_layout.addWidget(QLabel("Luma Messenger", objectName="AppTitle"))
        self.lbl_csv_name = QLabel("No CSV loaded", objectName="SubtitleLabel")
        self.lbl_csv_name.setWordWrap(True)
        sb_layout.addWidget(self.lbl_csv_name)

        sb_layout.addWidget(QLabel("EVENT CSV SOURCE", objectName="SectionHeader"))
        self.csv_combo = ModernComboBox()
        self.csv_combo.currentIndexChanged.connect(self._on_csv_selected)
        sb_layout.addWidget(self.csv_combo)

        # Stacked vertically: three buttons side by side don't fit the
        # 250 px sidebar and get clipped.
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        self.btn_folder = QPushButton("Folder...")
        self.btn_folder.clicked.connect(self._choose_folder)
        self.btn_browse = QPushButton("Open CSV...")
        self.btn_browse.clicked.connect(self._choose_single_csv)
        self.btn_reload = QPushButton("Reload")
        self.btn_reload.setToolTip("Re-read the current CSV from disk (picks up edits made outside the app)")
        self.btn_reload.clicked.connect(self._reload_current_csv)
        btn_col.addWidget(self.btn_folder)
        btn_col.addWidget(self.btn_browse)
        btn_col.addWidget(self.btn_reload)
        sb_layout.addLayout(btn_col)

        sb_layout.addWidget(QLabel("STATUS INCLUSION", objectName="SectionHeader"))
        self.chk_approved = QCheckBox("Approved Guests")
        self.chk_approved.setChecked(True)
        self.chk_approved.toggled.connect(self._rebuild_cohorts)

        self.chk_waitlist = QCheckBox("Waitlisted Guests")
        self.chk_waitlist.setChecked(True)
        self.chk_waitlist.toggled.connect(self._rebuild_cohorts)

        self.chk_hide_no_phone = QCheckBox("Hide Missing Phone Numbers")
        self.chk_hide_no_phone.setChecked(True)
        self.chk_hide_no_phone.toggled.connect(self._rebuild_cohorts)

        sb_layout.addWidget(self.chk_approved)
        sb_layout.addWidget(self.chk_waitlist)
        sb_layout.addWidget(self.chk_hide_no_phone)

        sb_layout.addWidget(QLabel("GROUP COHORTS BY", objectName="SectionHeader"))
        self.group_by_combo = ModernComboBox()
        self.group_by_combo.currentTextChanged.connect(self._rebuild_cohorts)
        sb_layout.addWidget(self.group_by_combo)

        sb_layout.addWidget(QLabel("MESSAGE COHORTS", objectName="SectionHeader"))
        self.cohort_list = QListWidget()
        self.cohort_list.currentItemChanged.connect(self._on_cohort_changed)
        sb_layout.addWidget(self.cohort_list, 1)

        main_layout.addWidget(sidebar)

        # --- Center + Right Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        center_wrap = QWidget()
        center_layout = QVBoxLayout(center_wrap)
        center_layout.setContentsMargins(16, 16, 12, 16)
        center_layout.setSpacing(12)

        # Roster Card
        roster_card = QFrame(objectName="Card")
        roster_layout = QVBoxLayout(roster_card)
        roster_layout.setContentsMargins(14, 14, 14, 14)
        roster_layout.setSpacing(10)

        roster_top = QHBoxLayout()
        self.lbl_cohort_header = QLabel("Recipients", objectName="TitleLabel")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name, phone, or label...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._refresh_table)

        self.btn_add_label = QPushButton("+ Label Selected")
        self.btn_add_label.clicked.connect(self._label_selected_rows)

        self.btn_select_all = QPushButton("Toggle All")
        self.btn_select_all.clicked.connect(self._toggle_all_checked)

        roster_top.addWidget(self.lbl_cohort_header)
        roster_top.addStretch()
        roster_top.addWidget(self.search_input)
        roster_top.addWidget(self.btn_add_label)
        roster_top.addWidget(self.btn_select_all)
        roster_layout.addLayout(roster_top)

        roster_tools = QHBoxLayout()
        self.btn_add_guest = QPushButton("+ Add Guest")
        self.btn_add_guest.clicked.connect(self._add_guest)
        self.btn_save_contacts = QPushButton("Save to Contacts")
        self.btn_save_contacts.clicked.connect(self._save_selected_to_contacts)
        roster_tools.addWidget(self.btn_add_guest)
        roster_tools.addWidget(self.btn_save_contacts)
        roster_tools.addStretch()
        roster_layout.addLayout(roster_tools)

        self.table = QTableWidget(0, 6)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.horizontalHeader().setFixedHeight(34)
        self.table.setHorizontalHeaderLabels(
            ["Send", "Name", "Phone", "Status", "Group", "Labels"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(2, 135)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 105)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._update_preview)
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        roster_layout.addWidget(self.table)

        center_layout.addWidget(roster_card, 3)

        # Composer Card
        comp_card = QFrame(objectName="Card")
        comp_layout = QVBoxLayout(comp_card)
        comp_layout.setContentsMargins(14, 14, 14, 14)
        comp_layout.setSpacing(8)

        comp_header = QHBoxLayout()
        self.lbl_composer_for = QLabel("MESSAGE TEMPLATE", objectName="SectionHeader")
        comp_header.addWidget(self.lbl_composer_for)
        comp_header.addStretch()
        self.lbl_char_count = QLabel("0 chars")
        self.lbl_char_count.setStyleSheet("color: #6E6E73; font-size: 11px;")
        comp_header.addWidget(self.lbl_char_count)
        comp_layout.addLayout(comp_header)

        self.token_bar = QHBoxLayout()
        self.token_bar.setSpacing(6)
        comp_layout.addLayout(self.token_bar)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Write message for this cohort... Use {first_name|there} for safe fallbacks. "
            "Add {qr_code} to attach the guest's ticket QR image."
        )
        self.editor.textChanged.connect(self._on_template_edited)
        comp_layout.addWidget(self.editor)

        action_row = QHBoxLayout()
        self.chk_dry_run = QCheckBox("Dry Run (Simulate without texting)")
        self.chk_dry_run.setChecked(True)

        self.chk_paste_qr = QCheckBox("Paste QR as inline image")
        self.chk_paste_qr.setToolTip(
            "Instead of attaching the QR as a file, paste it into Messages so it shows as a photo. "
            "Messages comes to the front for each QR — let the batch run without touching the Mac. "
            "Needs Accessibility permission the first time (System Settings → Privacy & Security → Accessibility)."
        )

        self.btn_send_selected = QPushButton("Send to Highlighted Rows (0)")
        self.btn_send_selected.clicked.connect(lambda: self._start_send(only_highlighted=True))

        self.btn_send_cohort = QPushButton("Send to Checked in Cohort (0)", objectName="PrimaryBtn")
        self.btn_send_cohort.clicked.connect(lambda: self._start_send(only_highlighted=False))

        action_row.addWidget(self.chk_dry_run)
        action_row.addWidget(self.chk_paste_qr)
        action_row.addStretch()
        action_row.addWidget(self.btn_send_selected)
        action_row.addWidget(self.btn_send_cohort)
        comp_layout.addLayout(action_row)

        center_layout.addWidget(comp_card, 2)
        splitter.addWidget(center_wrap)

        # --- Right Preview Inspector ---
        right_wrap = QWidget()
        right_wrap.setMinimumWidth(290)
        right_wrap.setMaximumWidth(350)
        right_layout = QVBoxLayout(right_wrap)
        right_layout.setContentsMargins(4, 16, 16, 16)
        right_layout.setSpacing(12)

        preview_card = QFrame(objectName="Card")
        pv_layout = QVBoxLayout(preview_card)
        pv_layout.setContentsMargins(16, 16, 16, 16)
        pv_layout.setSpacing(10)

        pv_layout.addWidget(QLabel("LIVE MESSAGE PREVIEW", objectName="SectionHeader"))
        self.lbl_preview_recipient = QLabel("To: —")
        self.lbl_preview_recipient.setStyleSheet("font-weight: 600; color: #1D1D1F;")
        pv_layout.addWidget(self.lbl_preview_recipient)

        bubble = QFrame(objectName="PreviewBubble")
        b_layout = QVBoxLayout(bubble)
        self.lbl_preview_body = QLabel("Type a message to preview...")
        self.lbl_preview_body.setObjectName("PreviewText")
        self.lbl_preview_body.setWordWrap(True)
        b_layout.addWidget(self.lbl_preview_body)
        pv_layout.addWidget(bubble)

        self.lbl_preview_hint = QLabel("Routes via iMessage automatically, falling back to SMS/RCS for Android numbers.")
        self.lbl_preview_hint.setWordWrap(True)
        self.lbl_preview_hint.setStyleSheet("color: #6E6E73; font-size: 11px; margin-top: 4px;")
        pv_layout.addWidget(self.lbl_preview_hint)

        pv_layout.addStretch()

        self.lbl_send_status = QLabel("Ready")
        self.lbl_send_status.setWordWrap(True)
        self.lbl_send_status.setStyleSheet("color: #6E6E73; font-size: 12px;")
        pv_layout.addWidget(self.lbl_send_status)

        right_layout.addWidget(preview_card)
        splitter.addWidget(right_wrap)

        main_layout.addWidget(splitter, 1)

    def set_dark_mode(self, dark: bool):
        """Apply the macOS system appearance; called at launch and on toggle."""
        self.dark_mode = dark
        muted = "#98989D" if dark else "#6E6E73"
        text = "#F5F5F7" if dark else "#1D1D1F"
        self.lbl_char_count.setStyleSheet(f"color: {muted}; font-size: 11px;")
        self.lbl_preview_recipient.setStyleSheet(f"font-weight: 600; color: {text};")
        self.lbl_preview_hint.setStyleSheet(f"color: {muted}; font-size: 11px; margin-top: 4px;")
        self.lbl_send_status.setStyleSheet(f"color: {muted}; font-size: 12px;")
        self._refresh_table()

    # --- Folder & CSV Ingestion ---
    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Luma CSVs", str(self.watch_dir))
        if folder:
            self.watch_dir = Path(folder)
            self._scan_folder(self.watch_dir)

    def _choose_single_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Luma Guest CSV", str(self.watch_dir), "CSV Files (*.csv)"
        )
        if path:
            p = Path(path)
            if self.csv_combo.findData(str(p)) == -1:
                self.csv_combo.addItem(p.name, str(p))
            self.csv_combo.setCurrentIndex(self.csv_combo.findData(str(p)))

    def _scan_folder(self, folder: Path):
        self.csv_combo.blockSignals(True)
        self.csv_combo.clear()
        csv_files = sorted(folder.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in csv_files:
            self.csv_combo.addItem(p.name, str(p))
        self.csv_combo.blockSignals(False)
        if csv_files:
            self._load_csv(csv_files[0])

    def _on_csv_selected(self, idx: int):
        data = self.csv_combo.itemData(idx)
        if data:
            self._load_csv(Path(data))

    def _reload_current_csv(self):
        """Re-read the current CSV from disk (picks up edits made outside the app)."""
        if self.current_csv_path:
            self._load_csv(self.current_csv_path)

    def _sidecar_path(self, csv_path: Path) -> Path:
        return csv_path.with_suffix(".labels.json")

    def _load_sidecar_state(self, csv_path: Path):
        sc = self._sidecar_path(csv_path)
        self.labels_map = {}
        self.checked_map = {}
        if sc.exists():
            try:
                data = json.loads(sc.read_text(encoding="utf-8"))
                # Support both older flat format and structured format
                if "labels" in data or "checked" in data:
                    self.labels_map = data.get("labels", {})
                    self.checked_map = data.get("checked", {})
                else:
                    self.labels_map = data
            except Exception:
                pass

    def _save_sidecar_state(self):
        if self.current_csv_path:
            sc = self._sidecar_path(self.current_csv_path)
            payload = {
                "labels": self.labels_map,
                "checked": self.checked_map,
            }
            sc.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_csv(self, path: Path):
        self.current_csv_path = path
        self.lbl_csv_name.setText(path.name)
        self._load_sidecar_state(path)

        loaded_rows: list[dict[str, str]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            self.columns = list(reader.fieldnames or [])
            for idx, raw in enumerate(reader):
                row = {k: (v or "").strip() for k, v in raw.items() if k is not None}
                if not row.get("first_name") and row.get("name"):
                    row["first_name"] = row["name"].split()[0]
                if not row.get("guest_id"):
                    row["guest_id"] = f"row-{idx}"
                gid = row["guest_id"]
                row["clean_phone"] = self._normalize_phone(row.get("phone_number", ""))
                row["custom_labels"] = ", ".join(self.labels_map.get(gid, []))
                if gid not in self.checked_map:
                    # Never auto-check: checking is only for picking a small
                    # subset within a cohort. Rows start unchecked.
                    self.checked_map[gid] = False
                loaded_rows.append(row)

        self.rows = loaded_rows
        self._populate_group_by_options()
        self._populate_token_chips()
        self._rebuild_cohorts()

    @staticmethod
    def _normalize_phone(raw: str) -> str:
        digits = re.sub(r"\D", "", str(raw))
        if len(digits) == 10:
            return f"+1{digits}"
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        return f"+{digits}" if digits else ""

    def _populate_group_by_options(self):
        self.group_by_combo.blockSignals(True)
        self.group_by_combo.clear()

        candidates = []
        if "ticket_name" in self.columns:
            candidates.append("ticket_name")
        if "approval_status" in self.columns:
            candidates.append("approval_status")
        candidates.append("custom_labels")

        for col in self.columns:
            if col in CORE_COLS or col in NOISE_EXACT or col.startswith(NOISE_PREFIXES):
                continue
            if col in ("clean_phone", "custom_labels"):
                continue
            distinct_vals = {r.get(col, "") for r in self.rows if r.get(col, "")}
            if 1 <= len(distinct_vals) <= 15:
                candidates.append(col)

        for c in candidates:
            self.group_by_combo.addItem(c)
        self.group_by_combo.blockSignals(False)

    def _populate_token_chips(self):
        while self.token_bar.count():
            item = self.token_bar.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        preferred = ["first_name", "name", "ticket_name", "approval_status", "qr_code_url"]
        custom_cols = [
            c for c in self.columns
            if c not in CORE_COLS and c not in NOISE_EXACT
            and not c.startswith(NOISE_PREFIXES)
            and c not in ("clean_phone", "custom_labels")
        ]
        for col in [c for c in preferred if c in self.columns] + custom_cols[:4]:
            btn = QPushButton(f"{{{col}}}", objectName="ChipBtn")
            btn.clicked.connect(lambda _, c=col: self.editor.insertPlainText(f"{{{c}}}"))
            self.token_bar.addWidget(btn)
        qr_btn = QPushButton("{qr_code}", objectName="ChipBtn")
        qr_btn.setToolTip("Attach the guest's ticket QR image (from qr_code_url)")
        qr_btn.clicked.connect(lambda: self.editor.insertPlainText("{qr_code}"))
        self.token_bar.addWidget(qr_btn)
        self.token_bar.addStretch()

    # --- Filtering & Cohort Routing ---
    def _filtered_rows(self) -> list[dict[str, str]]:
        allowed_statuses = set()
        if self.chk_approved.isChecked():
            allowed_statuses.add("approved")
        if self.chk_waitlist.isChecked():
            allowed_statuses.add("waitlist")

        out = []
        for r in self.rows:
            if "approval_status" in self.columns:
                if r.get("approval_status", "").lower() not in allowed_statuses:
                    continue
            if self.chk_hide_no_phone.isChecked() and not r.get("clean_phone"):
                continue
            out.append(r)
        return out

    def _rebuild_cohorts(self):
        sub = self._filtered_rows()
        group_col = self.group_by_combo.currentText() or "ticket_name"

        self.cohort_list.blockSignals(True)
        self.cohort_list.clear()

        all_item = QListWidgetItem(f"All Filtered ({len(sub)})")
        all_item.setData(Qt.UserRole, "__ALL__")
        self.cohort_list.addItem(all_item)

        if sub and (group_col in self.columns or group_col == "custom_labels"):
            if group_col == "custom_labels":
                tag_counts: Counter[str] = Counter()
                for r in sub:
                    for t in [x.strip() for x in r.get("custom_labels", "").split(",") if x.strip()]:
                        tag_counts[t] += 1
                for tag, cnt in sorted(tag_counts.items()):
                    it = QListWidgetItem(f"Label: {tag} ({cnt})")
                    it.setData(Qt.UserRole, f"LABEL::{tag}")
                    self.cohort_list.addItem(it)
            else:
                counts = Counter((r.get(group_col, "") or "(Blank)") for r in sub)
                for val, cnt in counts.most_common():
                    it = QListWidgetItem(f"{val} ({cnt})")
                    it.setData(Qt.UserRole, val)
                    self.cohort_list.addItem(it)

        self.cohort_list.blockSignals(False)
        self.cohort_list.setCurrentRow(0)
        self._on_cohort_changed(self.cohort_list.currentItem(), None)

    def _cohort_rows(self) -> list[dict[str, str]]:
        sub = self._filtered_rows()
        if not sub or self.active_cohort == "__ALL__":
            return sub

        group_col = self.group_by_combo.currentText()
        if self.active_cohort.startswith("LABEL::"):
            target_tag = self.active_cohort.split("::", 1)[1]
            return [
                r for r in sub
                if target_tag in [x.strip() for x in r.get("custom_labels", "").split(",")]
            ]

        if group_col in self.columns:
            return [r for r in sub if (r.get(group_col, "") or "(Blank)") == self.active_cohort]
        return sub

    def _on_cohort_changed(self, current: QListWidgetItem | None, _prev):
        if not current:
            return
        self.active_cohort = current.data(Qt.UserRole)
        self.lbl_cohort_header.setText(current.text())
        self.lbl_composer_for.setText(f"TEMPLATE FOR: {current.text().upper()}")

        self.editor.blockSignals(True)
        self.editor.setPlainText(self.group_templates.get(self.active_cohort, ""))
        self.editor.blockSignals(False)

        self._refresh_table()
        self._update_preview()

    # --- Table & Labels ---
    def _refresh_table(self):
        crows = self._cohort_rows()
        query = self.search_input.text().strip().lower()
        if query:
            crows = [
                r for r in crows
                if query in r.get("name", "").lower()
                or query in r.get("clean_phone", "")
                or query in r.get("custom_labels", "").lower()
            ]

        self.table.blockSignals(True)
        self.table.setRowCount(len(crows))

        for row_idx, row in enumerate(crows):
            gid = row.get("guest_id", "")
            phone = row.get("clean_phone", "")

            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            is_checked = self.checked_map.get(gid, False) and bool(phone)
            chk_item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
            chk_item.setData(Qt.UserRole, gid)
            self.table.setItem(row_idx, 0, chk_item)

            self.table.setItem(row_idx, 1, QTableWidgetItem(row.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(phone or "Missing"))

            status = row.get("approval_status", "")
            status_item = QTableWidgetItem(status)
            if status == "waitlist":
                status_item.setForeground(QColor("#FF9F0A" if self.dark_mode else "#C96A00"))
            elif status == "approved":
                status_item.setForeground(QColor("#30D158" if self.dark_mode else "#1E7E34"))
            status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row_idx, 3, status_item)

            ticket_item = QTableWidgetItem(row.get("ticket_name", ""))
            ticket_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row_idx, 4, ticket_item)
            labels_item = QTableWidgetItem(row.get("custom_labels", ""))
            labels_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row_idx, 5, labels_item)

        self.table.blockSignals(False)
        if crows:
            self.table.selectRow(0)
        self._update_counts()

    def _save_row_to_csv(self, gid: str, updates: dict[str, str]) -> bool:
        """Write a name/phone edit back to the loaded CSV so it survives reloads."""
        if not self.current_csv_path:
            return False
        try:
            with self.current_csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
            target = None
            if gid.startswith("row-"):
                try:
                    target = rows[int(gid[4:])]
                except (ValueError, IndexError):
                    target = None
            else:
                target = next((r for r in rows if (r.get("guest_id") or "").strip() == gid), None)
            if target is None:
                return False
            for key, val in updates.items():
                if key in fieldnames:
                    target[key] = val
            with self.current_csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
        except OSError:
            return False

    def _on_table_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            gid = item.data(Qt.UserRole)
            if gid:
                self.checked_map[gid] = (item.checkState() == Qt.Checked)
                self._save_sidecar_state()
        elif item.column() in (1, 2):
            gid = self.table.item(item.row(), 0).data(Qt.UserRole)
            row = self._find_row_by_id(gid) if gid else None
            if not row:
                return
            if item.column() == 1:
                new_name = item.text().strip()
                row["name"] = new_name
                row["first_name"] = new_name.split()[0] if new_name else ""
                if not self._save_row_to_csv(gid, {"name": new_name}):
                    QMessageBox.warning(
                        self, "Couldn't Save",
                        "The name was updated in the app, but the CSV file could not be written "
                        "(is it open in another program?).",
                    )
            else:
                raw_phone = item.text().strip()
                new_phone = self._normalize_phone(raw_phone)
                row["phone_number"] = raw_phone
                row["clean_phone"] = new_phone
                if not self._save_row_to_csv(gid, {"phone_number": raw_phone}):
                    QMessageBox.warning(
                        self, "Couldn't Save",
                        "The phone number was updated in the app, but the CSV file could not be written "
                        "(is it open in another program?).",
                    )
                # Show the normalized number (or Missing) and fix the checkbox.
                self.table.blockSignals(True)
                item.setText(new_phone or "Missing")
                if not new_phone:
                    chk = self.table.item(item.row(), 0)
                    chk.setCheckState(Qt.Unchecked)
                    self.checked_map[gid] = False
                    self._save_sidecar_state()
                self.table.blockSignals(False)
        self._update_counts()

    def _toggle_all_checked(self):
        any_unchecked = any(
            self.table.item(r, 0).checkState() == Qt.Unchecked
            for r in range(self.table.rowCount())
        )
        target = Qt.Checked if any_unchecked else Qt.Unchecked
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            if self.table.item(r, 2).text() != "Missing":
                item = self.table.item(r, 0)
                item.setCheckState(target)
                gid = item.data(Qt.UserRole)
                if gid:
                    self.checked_map[gid] = (target == Qt.Checked)
        self.table.blockSignals(False)
        self._save_sidecar_state()
        self._update_counts()

    def _label_selected_rows(self):
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not selected_rows:
            QMessageBox.information(self, "No Rows Selected", "Highlight one or more guests first.")
            return

        tag, ok = QInputDialog.getText(
            self, "Assign Contact Label", "Label name (e.g., VIP, Late Arrival, Bus Captain):"
        )
        tag = tag.strip()
        if not ok or not tag:
            return

        for r in selected_rows:
            gid = self.table.item(r, 0).data(Qt.UserRole)
            existing = self.labels_map.get(gid, [])
            if tag not in existing:
                existing.append(tag)
            self.labels_map[gid] = existing

        self._save_sidecar_state()
        for row in self.rows:
            row["custom_labels"] = ", ".join(self.labels_map.get(row["guest_id"], []))
        self._rebuild_cohorts()

    def _find_row_by_id(self, gid: str) -> dict[str, str] | None:
        for r in self.rows:
            if r.get("guest_id") == gid:
                return r
        return None

    # --- Add Guest & Contacts ---
    def _add_guest(self):
        """Add a custom guest (not in the Luma export) and append them to the CSV."""
        if not self.current_csv_path:
            QMessageBox.information(self, "No CSV Loaded", "Open a Luma CSV first, then add a guest to it.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Guest")
        form = QFormLayout(dialog)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Alex Rivera")
        phone_edit = QLineEdit()
        phone_edit.setPlaceholderText("e.g. (402) 555-0134")
        ticket_edit = QLineEdit()
        ticket_edit.setPlaceholderText("Optional - e.g. Bus Captain")
        status_combo = QComboBox()
        status_combo.addItems(["approved", "waitlist"])
        form.addRow("Name:", name_edit)
        form.addRow("Phone:", phone_edit)
        form.addRow("Ticket / group:", ticket_edit)
        form.addRow("Status:", status_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        if dialog.exec() != QDialog.Accepted:
            return

        name = name_edit.text().strip()
        phone = phone_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Enter a name for the guest.")
            return
        if not re.sub(r"\D", "", phone):
            QMessageBox.warning(self, "Missing Phone", "Enter a phone number so the guest can be texted.")
            return

        gid = f"manual-{int(time.time())}"
        row = {col: "" for col in self.columns}
        row.update({
            "guest_id": gid,
            "name": name,
            "first_name": name.split()[0],
            "phone_number": phone,
            "approval_status": status_combo.currentText(),
            "ticket_name": ticket_edit.text().strip(),
        })
        with self.current_csv_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writerow({col: row.get(col, "") for col in self.columns})

        self._load_csv(self.current_csv_path)
        self.lbl_send_status.setText(f"Added {name} to {self.current_csv_path.name}")

    def _save_selected_to_contacts(self):
        """Save the highlighted guests to macOS Contacts so they can be found later to text."""
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not selected_rows:
            QMessageBox.information(self, "No Rows Selected", "Highlight one or more guests first.")
            return
        created, existed, skipped = 0, 0, 0
        for r in selected_rows:
            gid = self.table.item(r, 0).data(Qt.UserRole)
            row_dict = self._find_row_by_id(gid)
            if not row_dict or not row_dict.get("clean_phone"):
                skipped += 1
                continue
            result = self._save_one_contact(row_dict.get("name", ""), row_dict["clean_phone"])
            if result == "created":
                created += 1
            elif result == "exists":
                existed += 1
            else:
                skipped += 1
        self.lbl_send_status.setText(
            f"Contacts - saved: {created}, already there: {existed}, skipped: {skipped}"
        )

    def _on_table_double_clicked(self, index):
        """Double-click a guest to save just that person to Contacts."""
        gid = self.table.item(index.row(), 0).data(Qt.UserRole)
        row_dict = self._find_row_by_id(gid)
        if not row_dict:
            return
        if not row_dict.get("clean_phone"):
            QMessageBox.information(
                self, "No Phone Number",
                f"{row_dict.get('name', '')} has no phone number to save.",
            )
            return
        result = self._save_one_contact(row_dict.get("name", ""), row_dict["clean_phone"])
        if result == "created":
            self.lbl_send_status.setText(f"Saved {row_dict.get('name', '')} to Contacts")
        elif result == "exists":
            self.lbl_send_status.setText(f"{row_dict.get('name', '')} is already in Contacts")
        else:
            QMessageBox.warning(
                self, "Could Not Save Contact",
                f"macOS Contacts did not accept {row_dict.get('name', '')}.",
            )

    @staticmethod
    def _save_one_contact(name: str, phone: str) -> str:
        """Add one person to macOS Contacts via AppleScript. Returns created/exists/failed."""
        parts = name.split()
        first = parts[0] if parts else name
        last = " ".join(parts[1:]) if len(parts) > 1 else ""
        applescript = """
        on run argv
            set firstName to item 1 of argv
            set lastName to item 2 of argv
            set phoneNumber to item 3 of argv
            if lastName = "" then
                set fullName to firstName
            else
                set fullName to firstName & " " & lastName
            end if
            tell application "Contacts"
                set matches to (every person whose name is fullName)
                if (count of matches) > 0 then
                    return "exists"
                end if
                set newPerson to make new person with properties {first name:firstName, last name:lastName}
                tell newPerson
                    make new phone with properties {label:"mobile", value:phoneNumber}
                end tell
                save
                return "created"
            end tell
        end run
        """
        try:
            proc = subprocess.run(
                ["osascript", "-e", applescript, first, last, phone],
                check=True, capture_output=True, text=True, timeout=30,
            )
            return proc.stdout.strip().strip('"') or "failed"
        except Exception:
            return "failed"

    # --- Template Rendering & Preview ---
    def _render_message(self, template: str, row_dict: dict[str, str]) -> str:
        def replacer(match):
            expr = match.group(1)
            if expr == "qr_code" or expr.startswith("qr_code:"):
                return ""  # QR image is attached separately, not pasted as text
            if "|" in expr:
                col, fallback = expr.split("|", 1)
            else:
                col, fallback = expr, ""
            val = str(row_dict.get(col.strip(), "")).strip()
            return val if val else fallback

        return re.sub(r"\{([^{}]+)\}", replacer, template)

    def _on_template_edited(self):
        text = self.editor.toPlainText()
        self.group_templates[self.active_cohort] = text
        self.lbl_char_count.setText(f"{len(text)} chars")
        self._update_preview()

    def _update_preview(self):
        self._update_counts()
        template = self.editor.toPlainText()
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if not selected_rows or self.table.rowCount() == 0:
            self.lbl_preview_recipient.setText("To: —")
            self.lbl_preview_body.setText(template or "Type a message to preview...")
            return

        r = selected_rows[0]
        gid = self.table.item(r, 0).data(Qt.UserRole)
        row_dict = self._find_row_by_id(gid)
        if not row_dict:
            return
        self.lbl_preview_recipient.setText(
            f"To: {row_dict.get('name', '')} ({row_dict.get('clean_phone', 'No Phone')})"
        )
        rendered = self._render_message(template, row_dict)
        self.lbl_preview_body.setText(rendered or "Type a message to preview...")
        if QR_TAG_RE.search(template):
            qr_url = self._qr_url_for_row(template, row_dict)
            if qr_url:
                jpg = _qr_jpg_for_url(qr_url)
                self.lbl_send_status.setText(
                    f"QR will attach: {jpg.name} ({jpg.stat().st_size // 1024} KB)"
                )
            else:
                self.lbl_send_status.setText("No QR link for this guest - image will be skipped")

    def _update_counts(self):
        checked = sum(
            1 for r in range(self.table.rowCount())
            if self.table.item(r, 0) and self.table.item(r, 0).checkState() == Qt.Checked
        )
        highlighted = len({idx.row() for idx in self.table.selectedIndexes()})
        self.btn_send_cohort.setText(f"Send to Checked in Cohort ({checked})")
        self.btn_send_selected.setText(f"Send to Highlighted Rows ({highlighted})")

    # --- Dispatch ---
    def _qr_url_for_row(self, template: str, row_dict: dict[str, str]) -> str | None:
        """URL for the {qr_code} tag: the row's qr_code_url, or {qr_code:<column>}."""
        m = QR_TAG_RE.search(template)
        if not m:
            return None
        col = m.group(1) or "qr_code_url"
        return (row_dict.get(col, "") or "").strip() or None

    def _start_send(self, only_highlighted: bool):
        template = self.editor.toPlainText().strip()
        if not template:
            QMessageBox.warning(self, "Empty Message", "Write a message template before sending.")
            return

        qr_wanted = QR_TAG_RE.search(template) is not None

        if only_highlighted:
            target_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        else:
            target_rows = [
                r for r in range(self.table.rowCount())
                if self.table.item(r, 0).checkState() == Qt.Checked
            ]

        queue = []
        for r in target_rows:
            gid = self.table.item(r, 0).data(Qt.UserRole)
            row_dict = self._find_row_by_id(gid)
            if not row_dict or not row_dict.get("clean_phone"):
                continue
            qr_path = None
            if qr_wanted:
                qr_url = self._qr_url_for_row(template, row_dict)
                if qr_url:
                    qr_path = _qr_jpg_for_url(qr_url)
            queue.append({
                "name": row_dict.get("name", ""),
                "phone": row_dict["clean_phone"],
                "message": self._render_message(template, row_dict),
                "qr_wanted": qr_wanted,
                "qr_path": str(qr_path) if qr_path else None,
            })

        if not queue:
            QMessageBox.information(self, "No Valid Recipients", "No recipients with valid phone numbers selected.")
            return

        dry_run = self.chk_dry_run.isChecked()
        mode_str = "DRY RUN" if dry_run else "LIVE IMESSAGE/SMS"
        confirm = QMessageBox.question(
            self,
            "Confirm Batch Send",
            f"Mode: {mode_str}\nRecipients: {len(queue)}\n\nProceed?",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        if dry_run:
            dlg = DryRunPreviewDialog(queue, self)
            dlg.exec()
            if dlg.send_real:
                confirm_live = QMessageBox.question(
                    self,
                    "Confirm Live Send",
                    f"Mode: LIVE IMESSAGE/SMS\nRecipients: {len(queue)}\n\nProceed?",
                )
                if confirm_live != QMessageBox.StandardButton.Yes:
                    self.lbl_send_status.setText("Live send cancelled — nothing sent")
                    return
                self._start_live_send(queue)
            else:
                self.lbl_send_status.setText(
                    f"Dry run previewed {len(queue)} recipient(s) — nothing sent"
                )
            return

        self._start_live_send(queue)

    def _start_live_send(self, queue):
        self.btn_send_cohort.setEnabled(False)
        self.btn_send_selected.setEnabled(False)
        self.worker = MessageSenderWorker(queue, dry_run=False, qr_via_paste=self.chk_paste_qr.isChecked())
        self.worker.progress.connect(
            lambda cur, tot, name, st: self.lbl_send_status.setText(f"[{cur}/{tot}] {name}: {st}")
        )
        self.worker.finished_batch.connect(self._on_send_finished)
        self.worker.start()

    def _on_send_finished(self, sent: int, failed: int):
        self.btn_send_cohort.setEnabled(True)
        self.btn_send_selected.setEnabled(True)
        self.lbl_send_status.setText(f"Completed — Sent: {sent}, Failed: {failed}")
        if getattr(self.worker, "paste_blocked_reason", None):
            QMessageBox.warning(
                self,
                "QR paste blocked",
                "The text messages went out, but no QR images were pasted.\n\n"
                f"{self.worker.paste_blocked_reason}",
            )


def _apply_theme(app: QApplication, win: "LumaMessengerWindow | None" = None) -> None:
    """Pick the light/dark palette from the macOS system appearance."""
    try:
        dark = QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        dark = False
    app.setStyleSheet(build_qss(DARK_PALETTE if dark else LIGHT_PALETTE))
    if win is not None:
        win.set_dark_mode(dark)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LumaMessengerWindow()
    _apply_theme(app, win)
    try:
        QApplication.styleHints().colorSchemeChanged.connect(
            lambda _scheme: _apply_theme(app, win)
        )
    except Exception:
        pass  # Older Qt: the theme is fixed at launch instead of live-switching.
    win.show()
    sys.exit(app.exec())
