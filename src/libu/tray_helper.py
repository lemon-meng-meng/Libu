# SPDX-License-Identifier: GPL-3.0-or-later
"""吏部 · 截屏 OCR 托盘助手。

一个独立的轻量进程：在系统托盘显示吏部图标，点击「截屏OCR」后用鼠标在屏幕上
框选区域，截图交给本地后端做 OCR，并把识别结果写入剪贴板与吏部的截屏页面。

依赖系统提供的 GTK3 / PyGObject（deb 包会声明依赖）。在没有 GTK 或 Wayland
禁止读取根窗口时，会尝试 gnome-screenshot / grim / ImageMagick import 等工具兜底。

用法：
    python3 -m libu.tray_helper             # 显示托盘
    python3 -m libu.tray_helper --capture   # 直接进入区域截屏（不常驻）
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]
ICON_CANDIDATES = [
    APP_ROOT / "data" / "icons" / "libu_64.png",
    APP_ROOT / "data" / "icons" / "libu.png",
    Path("/usr/share/icons/hicolor/256x256/apps/libu.png"),
]


def _icon_path() -> str:
    for p in ICON_CANDIDATES:
        if p.is_file():
            return str(p)
    return ""


# --------------------------------------------------------------------------- #
# 配置读取
# --------------------------------------------------------------------------- #
def _data_dir() -> Path:
    return Path.home() / ".libu"


def _screenshot_dir() -> Path:
    d = _data_dir() / "screenshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _request_file() -> Path:
    return _data_dir() / "screenshot.request"


def _settings() -> dict:
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "libu" / "settings.json"
    try:
        return json.loads(cfg.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _feature_backend() -> str:
    """读取 settings.json 中截屏 OCR 指定的引擎。"""
    data = _settings()
    fb = data.get("feature_backends") or {}
    return (fb.get("screenshot") or data.get("default_backend") or "").strip()


def _screenshot_hotkey() -> str:
    return (_settings().get("screenshot_hotkey") or "Ctrl+Alt+O").strip()


# --------------------------------------------------------------------------- #
# 全局快捷键（X11）
# --------------------------------------------------------------------------- #
_MOD_ORDER = [
    ("<Control>", "ctrl"),
    ("<Alt>", "alt"),
    ("<Shift>", "shift"),
    ("<Super>", "super"),
]


def _to_gtk_accel(spec: str) -> str:
    """把 Ctrl+Alt+O 转成 GTK 的 <Control><Alt>O 形式。"""
    mods = []
    key = ""
    for part in (spec or "").split("+"):
        p = part.strip()
        low = p.lower()
        if low in ("ctrl", "control"):
            mods.append("<Control>")
        elif low == "alt":
            mods.append("<Alt>")
        elif low == "shift":
            mods.append("<Shift>")
        elif low in ("super", "win", "meta", "cmd", "command"):
            mods.append("<Super>")
        elif p:
            key = p.upper()
    return "".join(mods) + key


def _register_hotkey_keybinder(spec: str, callback) -> bool:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Keybinder", "3.0")
    from gi.repository import Keybinder

    Keybinder.init()
    return bool(Keybinder.bind(_to_gtk_accel(spec), callback))


def _register_hotkey_xlib(spec: str, callback) -> bool:
    from Xlib import X, XK, display

    key = ""
    mods = 0
    for part in (spec or "").split("+"):
        p = part.strip()
        low = p.lower()
        if low in ("ctrl", "control"):
            mods |= X.ControlMask
        elif low == "alt":
            mods |= X.Mod1Mask
        elif low == "shift":
            mods |= X.ShiftMask
        elif low in ("super", "win", "meta", "cmd", "command"):
            mods |= X.Mod4Mask
        elif p:
            key = p.lower()
    if not key:
        return False
    keysym_name = {"escape": "Escape", "space": "space", "print": "Print"}.get(key, key)
    keysym = XK.string_to_keysym(keysym_name)
    if not keysym:
        return False
    disp = display.Display()
    keycode = disp.keysym_to_keycode(keysym)
    root = disp.screen().root
    root.grab_key(keycode, mods, True, X.GrabModeAsync, X.GrabModeAsync)
    disp.sync()

    import threading

    from gi.repository import GLib

    def loop():
        while True:
            try:
                event = disp.next_event()
            except Exception:  # noqa: BLE001
                return
            if event.type == X.KeyPress:
                GLib.idle_add(callback)

    threading.Thread(target=loop, daemon=True).start()
    return True


def _register_hotkey(spec: str, callback) -> bool:
    """注册全局快捷键，优先 keybinder，其次 X11（Xlib）。Wayland 下通常不可用。"""
    for attempt in (_register_hotkey_keybinder, _register_hotkey_xlib):
        try:
            if attempt(spec, callback):
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def _api_bases() -> list[str]:
    bases = []
    env = os.environ.get("LIBU_API")
    if env:
        bases.append(env.rstrip("/"))
    port = os.environ.get("LIBU_PORT")
    if port:
        bases.append(f"http://127.0.0.1:{port}")
    bases += ["http://127.0.0.1:8756", "http://127.0.0.1:8000"]
    seen, out = set(), []
    for b in bases:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def _post_ingest(image_path: str) -> str:
    """把截图交给后端 OCR，返回识别文本（失败返回空串）。"""
    payload = json.dumps({
        "path": image_path,
        "backend": _feature_backend() or None,
    }).encode("utf-8")
    for base in _api_bases():
        try:
            req = urllib.request.Request(
                base + "/screenshot/ingest",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("text", "") or ""
        except Exception:  # noqa: BLE001
            continue
    return ""


# --------------------------------------------------------------------------- #
# 截屏
# --------------------------------------------------------------------------- #
def _grab_via_tools() -> str | None:
    """使用系统工具截全屏，返回临时文件路径。"""
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    commands = [
        ["gnome-screenshot", "-f", tmp],
        ["grim", tmp],
        ["spectacle", "-b", "-n", "-o", tmp],
        ["import", "-window", "root", tmp],
        ["scrot", tmp],
    ]
    for cmd in commands:
        if not shutil.which(cmd[0]):
            continue
        try:
            subprocess.run(cmd, check=True, timeout=30)
            if Path(tmp).stat().st_size > 0:
                return tmp
        except Exception:  # noqa: BLE001
            continue
    try:
        Path(tmp).unlink(missing_ok=True)
    except OSError:
        pass
    return None


def _process_capture(pixbuf_or_path):
    """统一处理截取结果：保存、OCR、复制到系统剪贴板、通知前端。"""
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gtk

    out = _screenshot_dir() / f"{uuid.uuid4().hex[:12]}.png"
    if hasattr(pixbuf_or_path, "savev"):
        pixbuf_or_path.savev(str(out), "png", [], [])
    else:
        shutil.copyfile(str(pixbuf_or_path), str(out))

    text = _post_ingest(str(out))
    if text:
        try:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            clipboard.store()
        except Exception:  # noqa: BLE001
            pass
    return str(out), text


def capture_region() -> tuple[str, str]:
    """显示全屏遮罩让用户框选，返回 (图片路径, 识别文本)。"""
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, GdkPixbuf, Gtk

    screen = Gdk.Screen.get_default()
    root = Gdk.get_default_root_window()
    width = screen.get_width()
    height = screen.get_height()
    shot = Gdk.pixbuf_get_from_window(root, 0, 0, width, height)

    if shot is None:
        # Wayland/无根窗口权限：退回系统工具（全屏）
        path = _grab_via_tools()
        if not path:
            return "", ""
        return _process_capture(path)

    state = {"start": None, "end": None, "done": None}
    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_decorated(False)
    win.set_keep_above(True)
    win.set_app_paintable(True)
    win.fullscreen()
    win.set_can_focus(True)

    area = Gtk.DrawingArea()
    win.add(area)

    def select_rect():
        s, e = state["start"], state["end"]
        if not s or not e:
            return None
        x = max(0, min(s[0], e[0]))
        y = max(0, min(s[1], e[1]))
        w = min(width, abs(e[0] - s[0]))
        h = min(height, abs(e[1] - s[1]))
        if w < 3 or h < 3:
            return None
        return x, y, w, h

    def on_draw(_widget, cr):
        Gdk.cairo_set_source_pixbuf(cr, shot, 0, 0)
        cr.paint()
        cr.set_source_rgba(0, 0, 0, 0.45)
        cr.paint()
        rect = select_rect()
        if rect:
            x, y, w, h = rect
            Gdk.cairo_set_source_pixbuf(cr, shot, 0, 0)
            cr.rectangle(x, y, w, h)
            cr.fill()
            cr.set_source_rgba(0.43, 0.66, 1.0, 1.0)
            cr.set_line_width(2)
            cr.rectangle(x, y, w, h)
            cr.stroke()
            cr.set_source_rgba(1, 1, 1, 0.95)
            cr.select_font_face("Sans")
            cr.set_font_size(14)
            cr.move_to(x + 6, y - 8 if y > 20 else y + 20)
            cr.show_text(f"{w} × {h}")
        return False

    area.connect("draw", on_draw)

    def on_press(_w, event):
        if event.button == 1:
            state["start"] = (event.x_root, event.y_root)
            state["end"] = (event.x_root, event.y_root)

    def on_motion(_w, event):
        if state["start"]:
            state["end"] = (event.x_root, event.y_root)
            area.queue_draw()

    def on_release(_w, event):
        if event.button != 1:
            return
        state["end"] = (event.x_root, event.y_root)
        rect = select_rect()
        if rect:
            state["done"] = rect
        Gtk.main_quit()

    def on_key(_w, event):
        if event.keyval == Gdk.KEY_Escape:
            state["done"] = None
            Gtk.main_quit()

    area.add_events(
        Gdk.EventMask.BUTTON_PRESS_MASK
        | Gdk.EventMask.BUTTON_RELEASE_MASK
        | Gdk.EventMask.POINTER_MOTION_MASK
    )
    area.connect("button-press-event", on_press)
    area.connect("button-release-event", on_release)
    area.connect("motion-notify-event", on_motion)
    win.connect("key-press-event", on_key)
    win.connect("destroy", lambda *_: Gtk.main_quit())
    win.show_all()
    try:
        win.present()
    except Exception:  # noqa: BLE001
        pass
    Gtk.main()

    rect = state.get("done")
    if not rect:
        return "", ""
    x, y, w, h = rect
    crop = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, shot.get_has_alpha(), 8, w, h)
    shot.copy_area(x, y, w, h, crop, 0, 0)
    return _process_capture(crop)


# --------------------------------------------------------------------------- #
# 托盘
# --------------------------------------------------------------------------- #
def run_tray():
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk

    def do_capture(*_):
        try:
            capture_region()
        except Exception as exc:  # noqa: BLE001
            print(f"[libu-tray] 截屏失败：{exc}", file=sys.stderr)

    def open_app(*_):
        port = os.environ.get("LIBU_PORT", "8756")
        url = f"http://127.0.0.1:{port}/"
        for cmd in (["xdg-open", url], ["gio", "open", url]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.Popen(cmd)
                    return
                except Exception:  # noqa: BLE001
                    pass

    def quit_app(*_):
        Gtk.main_quit()

    indicator = None
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3

        indicator = AppIndicator3.Indicator.new(
            "libu-tray", _icon_path() or "image-x-generic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        menu = Gtk.Menu()
        item_cap = Gtk.MenuItem(label="截屏 OCR")
        item_cap.connect("activate", do_capture)
        item_open = Gtk.MenuItem(label="打开吏部")
        item_open.connect("activate", open_app)
        item_quit = Gtk.MenuItem(label="退出")
        item_quit.connect("activate", quit_app)
        for it in (item_cap, item_open, Gtk.SeparatorMenuItem(), item_quit):
            menu.append(it)
        menu.show_all()
        indicator.set_menu(menu)
    except Exception:  # noqa: BLE001
        # 回退到 Gtk.StatusIcon
        status = Gtk.StatusIcon()
        if _icon_path():
            status.set_from_file(_icon_path())
        else:
            status.set_from_stock(Gtk.STOCK_EXECUTE)
        status.set_tooltip_text("吏部 · 截屏 OCR")
        status.connect("activate", do_capture)
        menu = Gtk.Menu()
        item_cap = Gtk.MenuItem(label="截屏 OCR")
        item_cap.connect("activate", do_capture)
        item_quit = Gtk.MenuItem(label="退出")
        item_quit.connect("activate", quit_app)
        menu.append(item_cap)
        menu.append(item_quit)
        menu.show_all()
        status.connect("popup-menu", lambda icon, button, t: menu.popup(None, None, None, None, button, t))

    # 注册全局快捷键（截屏 OCR）
    hotkey = _screenshot_hotkey()
    if not _register_hotkey(hotkey, do_capture):
        print(
            f"[libu-tray] 未能注册全局快捷键 {hotkey}（Wayland 环境或不支持），"
            "可改用托盘菜单「截屏 OCR」",
            file=sys.stderr,
        )
    else:
        print(f"[libu-tray] 已注册截屏快捷键 {hotkey}", file=sys.stderr)

    # 轮询前端写入的截屏请求
    def poll_request():
        req = _request_file()
        if req.exists():
            try:
                req.unlink()
            except OSError:
                pass
            do_capture()
        return True

    GLib.timeout_add(800, poll_request)
    Gtk.main()


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--capture" in argv:
        path, text = capture_region()
        if text:
            print(text)
        return 0 if path else 1
    run_tray()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
