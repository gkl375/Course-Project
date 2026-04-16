"""Center Toplevel dialogs over the main application window."""

from __future__ import annotations

import tkinter as tk


def style_popup_window(
    window: tk.Toplevel,
    parent: tk.Misc,
    *,
    resizable: bool = False,
    toolwindow: bool = False,
) -> None:
    """Child of main window. If ``toolwindow`` is True (Windows), ``-toolwindow`` drops min/max buttons."""
    top = parent.winfo_toplevel()
    window.transient(top)
    window.resizable(bool(resizable), bool(resizable))
    if toolwindow:
        try:
            window.attributes("-toolwindow", True)
        except tk.TclError:
            pass


def _parse_geometry_wh(geom: str) -> tuple[int, int] | None:
    """Parse 'WxH' or 'WxH+X+Y' into (width, height)."""
    if not geom:
        return None
    try:
        wh = geom.split("+", 1)[0].strip()
        w_s, h_s = wh.split("x", 1)
        w, h = int(w_s), int(h_s)
        if w > 0 and h > 0:
            return w, h
    except (ValueError, IndexError):
        pass
    return None


def center_toplevel(window: tk.Toplevel, parent: tk.Misc | None = None) -> None:
    """Position *window* centered over the main *parent* window (usually ``self.root``).

    Uses ``wm_geometry()`` / ``geometry()`` so sizes match what Tk uses, and schedules
    several passes so layout is finished before measuring (Windows often reports 1×1
    until the window is mapped).
    """
    p = parent if parent is not None else window.master

    def _apply() -> None:
        try:
            if not window.winfo_exists():
                return
        except tk.TclError:
            return

        window.update_idletasks()
        try:
            p.update_idletasks()
        except tk.TclError:
            return

        cg = window.geometry()
        parsed = _parse_geometry_wh(cg)
        if parsed:
            ww, wh = parsed
        else:
            ww = max(window.winfo_width(), window.winfo_reqwidth())
            wh = max(window.winfo_height(), window.winfo_reqheight())

        if ww < 2 or wh < 2:
            ww = max(ww, window.winfo_reqwidth())
            wh = max(wh, window.winfo_reqheight())
        if ww < 2 or wh < 2:
            return

        try:
            root = p.winfo_toplevel()
            root.update_idletasks()
            rg = root.wm_geometry()
        except tk.TclError:
            return

        rp = _parse_geometry_wh(rg)
        if rp:
            pw, ph = rp
        else:
            pw = max(root.winfo_width(), root.winfo_reqwidth())
            ph = max(root.winfo_height(), root.winfo_reqheight())

        if pw < 2 or ph < 2:
            return

        try:
            px = root.winfo_rootx()
            py = root.winfo_rooty()
        except tk.TclError:
            return

        x = int(px + (pw - ww) / 2)
        y = int(py + (ph - wh) / 2)

        try:
            sw = window.winfo_screenwidth()
            sh = window.winfo_screenheight()
            x = max(0, min(x, max(0, sw - ww)))
            y = max(0, min(y, max(0, sh - wh)))
        except tk.TclError:
            pass

        # Set full WxH+X+Y so size is preserved (some platforms mishandle "+x+y" only).
        window.geometry(f"{ww}x{wh}+{x}+{y}")

    def _on_map(_event: tk.Event | None = None) -> None:
        window.after_idle(_apply)

    window.bind("<Map>", _on_map, add=True)
    window.after_idle(lambda: window.after_idle(_apply))
    window.after(50, _apply)
    window.after(160, _apply)
