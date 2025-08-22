#.===============================================================
#. --- Advanced Facebook Downloader (FBx4simo) v1.0.0 ---
#. --- CREATED BY : ISLAM ALBADAWY ---
#. --- ASCII icons/colors + robust FB fixes (watch/fb.watch) ---
#.===============================================================

import os
import sys
import shutil
import zipfile
import platform
import subprocess
import urllib.request
import tarfile
from urllib.parse import urlparse, parse_qs, urlunparse

# -------------------------
# ASCII Icons (CMD-safe)
# -------------------------
ICON = {
    "url":   "[URL]",
    "ok":    "[OK]",
    "err":   "[ERR]",
    "warn":  "[!]",
    "dl":    "[DL]",
    "tip":   "[TIP]",
    "prompt": ">"
}

# -------------------------
# Auto-install required packages (yt-dlp, colorama, pyfiglet)
# -------------------------
def ensure_pip_package(pkg: str, import_name: str = None, upgrade: bool = False):
    import importlib
    modname = import_name or pkg
    try:
        importlib.import_module(modname)
        return True
    except ImportError:
        pass

    print(f"{ICON['tip']} Installing '{pkg}' ...")
    args = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        args.append("-U")
    args.append(pkg)
    try:
        subprocess.run(args, check=True)
    except Exception as e:
        print(f"{ICON['err']} Failed to install {pkg}: {e}")
        return False

    try:
        importlib.import_module(modname)
        return True
    except ImportError:
        print(f"{ICON['err']} Could not import {modname} after installation.")
        return False

# Required
ensure_pip_package("yt-dlp", "yt_dlp", upgrade=True)
# Optional
ensure_pip_package("colorama", "colorama", upgrade=False)
ensure_pip_package("pyfiglet", "pyfiglet", upgrade=False)

from yt_dlp import YoutubeDL, utils as ytdlp_utils
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:
    class _Dummy:
        RESET_ALL = ''
        RED = YELLOW = GREEN = CYAN = MAGENTA = BLUE = WHITE = ''
        BRIGHT = NORMAL = DIM = ''
    Fore = _Dummy()
    Style = _Dummy()

TITLE_COLOR = getattr(Fore, "CYAN", "") + getattr(Style, "BRIGHT", "")
BAR_COLOR   = getattr(Fore, "YELLOW", "") + getattr(Style, "BRIGHT", "")
PATH_COLOR  = getattr(Fore, "MAGENTA", "") + getattr(Style, "BRIGHT", "")
LBL_COLOR   = getattr(Fore, "WHITE", "") + getattr(Style, "BRIGHT", "")
RST         = getattr(Style, "RESET_ALL", "")

# ---------------------------------
# CWD = script dir
# ---------------------------------
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------
# Progress bar helpers
# ---------------------------------
USE_ASCII = os.environ.get("ASCII", "0") == "1" or os.environ.get("NO_UNICODE", "0") == "1"

def _charset():
    if USE_ASCII:
        return "#", "-"
    try:
        ("█").encode(sys.stdout.encoding or "utf-8")
        return "█", "·"
    except Exception:
        return "#", "-"

FULL_CH, EMPTY_CH = _charset()

def _bar(percent: float, width: int = 30) -> str:
    p = max(0.0, min(100.0, percent))
    filled = int(width * p / 100.0)
    return f"[{FULL_CH*filled}{EMPTY_CH*(width-filled)}] {p:5.1f}%"

def _reporthook_builder(label: str):
    last_percent = -1
    def _hook(block_count, block_size, total_size):
        nonlocal last_percent
        downloaded = block_count * block_size
        if total_size > 0:
            percent = min(100.0, downloaded * 100.0 / total_size)
            if int(percent) != int(last_percent):
                last_percent = percent
                print(f"\r{label} {BAR_COLOR}{_bar(percent)}{RST}", end="", flush=True)
            if downloaded >= total_size:
                print(f"\r{label} {BAR_COLOR}{_bar(100.0)}{RST}", flush=True)
        else:
            mb = downloaded / (1024*1024)
            print(f"\r{label} {mb:.1f} MB...", end="", flush=True)
    return _hook

# ---------------------------------
# Banner
# ---------------------------------
def print_banner():
    import shutil as _shutil
    cols = max(60, _shutil.get_terminal_size((100, 20)).columns)
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA, Fore.BLUE]
    try:
        from pyfiglet import Figlet
        f1 = Figlet(font="slant")
        f2 = Figlet(font="standard")
        text1 = f1.renderText("FACEBOOK DOWNLOADER")
        text2 = f2.renderText("V1.0.0")
        lines = (text1 + text2).splitlines()
    except Exception:
        lines = r"""
__     __  _   _ _   _ ______ _   _ ____   ____   ____   ____  _   _ _   _ _   _ ____   ____   ____  
\ \   / / | | | | \ | |  ____| \ | |  _ \ |  _ \ / __ \ | \ \ | \ | | \ | | \ | |  _ \ / __ \ / __ \ 
 \ \ / /  | | | |  \| | |__  |  \| | | | || | | | |  | | | \ \|  \| |  \| |  \| | | | | |  | | |  | |
  \ V /   | |_| | |\  |  __| | |\  | |_| || |_| | |__| | | |\ \ |\  | |\  | |\  | |_| | |__| | |__| |
   \_/     \___/ |_| \_|_|    |_| \_|____/ |____/ \____/  |_| \_\_| \_|_| \_|_| \_|____/ \____/ \____/
""".splitlines()
    print()
    for i, line in enumerate(lines):
        c = colors[i % len(colors)]
        print(c + Style.BRIGHT + line.center(cols) + Style.RESET_ALL)
    print()
    print(" =============================================================== ")
    print(" --- FACEBOOK DOWNLOADER 'FBx4simo' V1.0.0 ---- ")
    print(" --- CREATED BY : ISLAM ALBADAWY ---")
    print(" ========================================================\n ")

# ---------------------------------
# Paths & FFmpeg
# ---------------------------------
def get_script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def get_save_folder() -> str:
    save_path = os.path.join(get_script_dir(), "Videos")
    os.makedirs(save_path, exist_ok=True)
    return save_path

def ffmpeg_path() -> str:
    if platform.system().lower() == "windows":
        return os.path.join(get_script_dir(), "ffmpeg", "ffmpeg.exe")
    else:
        return os.path.join(get_script_dir(), "ffmpeg", "ffmpeg")

def check_ffmpeg() -> str:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return "ffmpeg"
    except Exception:
        pass

    local_ff = ffmpeg_path()
    if os.path.exists(local_ff):
        return local_ff

    print(f"{ICON['warn']} ffmpeg not found. Downloading a portable version...")

    ffmpeg_dir = os.path.join(get_script_dir(), "ffmpeg")
    os.makedirs(ffmpeg_dir, exist_ok=True)

    system_name = platform.system().lower()
    if system_name == "windows":
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
        urllib.request.urlretrieve(url, zip_path, _reporthook_builder(f"{ICON['dl']} Downloading ffmpeg (Windows)"))
        print(" - Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        os.remove(zip_path)

        moved = False
        for root, _, files in os.walk(ffmpeg_dir):
            if "ffmpeg.exe" in files:
                src = os.path.join(root, "ffmpeg.exe")
                dst = os.path.join(ffmpeg_dir, "ffmpeg.exe")
                if src != dst:
                    shutil.move(src, dst)
                moved = True
                break
        if not moved:
            raise RuntimeError("Could not locate ffmpeg.exe inside the downloaded archive.")
        return os.path.join(ffmpeg_dir, "ffmpeg.exe")
    else:
        url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        tar_path = os.path.join(ffmpeg_dir, "ffmpeg.tar.xz")
        urllib.request.urlretrieve(url, tar_path, _reporthook_builder(f"{ICON['dl']} Downloading ffmpeg (Unix)"))
        print(" - Extracting...")
        with tarfile.open(tar_path, "r:xz") as tar_ref:
            tar_ref.extractall(ffmpeg_dir)
        os.remove(tar_path)

        moved = False
        for root, _, files in os.walk(ffmpeg_dir):
            if "ffmpeg" in files and not root.endswith("doc"):
                src = os.path.join(root, "ffmpeg")
                dst = os.path.join(ffmpeg_dir, "ffmpeg")
                if src != dst:
                    shutil.move(src, dst)
                try:
                    os.chmod(dst, 0o755)
                except Exception:
                    pass
                moved = True
                break
        if not moved:
            raise RuntimeError("Could not locate ffmpeg binary inside the downloaded archive.")
        return os.path.join(ffmpeg_dir, "ffmpeg")

# ---------------------------------
# FB helpers (URL + privacy detect)
# ---------------------------------
def is_facebook(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(d in host for d in ("facebook.com", "fb.watch", "m.facebook.com", "mbasic.facebook.com"))

def normalize_fb_url(url: str) -> str:
    """
    Support:
      - https://www.facebook.com/watch?v=ID
      - https://www.facebook.com/watch/?v=ID
      - https://fb.watch/XXXX/
    """
    try:
        u = urlparse(url)
        scheme = "https"
        netloc = u.netloc.lower()
        path = u.path
        query = u.query

        if "fb.watch" in netloc:
            # Keep it as is (yt-dlp can resolve it); just enforce https
            return urlunparse((scheme, netloc, path, "", "", ""))

        if "facebook.com" in netloc:
            qs = parse_qs(query)
            if "/watch" in path and "v" in qs and qs["v"]:
                vid = qs["v"][0]
                # Prefer canonical watch?v=ID
                return f"https://www.facebook.com/watch?v={vid}"
        return url
    except Exception:
        return url

PRIVATE_HINTS = (
    "login", "log in", "logged in", "cookies", "cookie", "private",
    "only available to registered", "you must be logged in",
    "permissions", "session expired", "this content isn't available",
    "not available right now"
)

def looks_private_error(err: Exception) -> bool:
    msg = str(err).lower()
    return any(h in msg for h in PRIVATE_HINTS)

# ---------------------------------
# Format selection
# ---------------------------------
def build_format_selector(choice: str) -> str:
    mapping = {"1": 360, "2": 480, "3": 720, "4": 1080}
    if choice in mapping:
        h = mapping[choice]
        # Prefer MP4 and provide robust fallbacks
        return (
            f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/"
            f"bv*[height<={h}]+ba/"
            f"b[height<={h}][ext=mp4]/"
            f"b[height<={h}]/"
            "best[ext=mp4]/best"
        )
    elif choice in {"5", "7", "8"}:
        return "best[ext=mp4]/best"
    elif choice == "6":
        return "bestaudio/best"
    else:
        return "best[ext=mp4]/best"

def pick_best_match_format_id(info: dict, preferred_h: int | None):
    """
    Try to choose a suitable `format_id` from available formats to avoid
    'Requested format is not available'.
    Strategy:
      - Prefer progressive MP4 (video+audio in one stream).
      - If preferred height is set, pick the closest <= preferred height.
      - If none <= preferred, pick the closest by absolute difference.
      - If nothing matches, let yt-dlp choose 'best'.
    """
    fmts = info.get("formats") or []
    def h_val(f): return f.get("height") or 0

    # Prefer progressive MP4 (contains both video and audio)
    prog = [f for f in fmts if f.get("ext") == "mp4" and f.get("vcodec") != "none" and f.get("acodec") != "none"]

    if preferred_h:
        cand = sorted([f for f in prog if h_val(f) and h_val(f) <= preferred_h], key=lambda f: h_val(f))
        if cand:
            return cand[-1].get("format_id")
        cand = sorted([f for f in prog if h_val(f)], key=lambda f: abs(h_val(f) - preferred_h))
        if cand:
            return cand[0].get("format_id")

    if prog:
        return sorted(prog, key=lambda f: h_val(f) or 0)[-1].get("format_id")

    return None

# ---------------------------------
# Title + progress
# ---------------------------------
def try_print_title(url: str, ffmpeg_loc: str | None = None):
    try:
        with YoutubeDL({
            "quiet": True,
            "no_warnings": True,
            "http_headers": {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.5"},
            "ffmpeg_location": ffmpeg_loc or "ffmpeg"
        }) as ydl:
            info = ydl.extract_info(url, download=False)
        if info.get("_type") == "playlist":
            title = info.get("title") or "Playlist"
            count = len(info.get("entries") or []) if info.get("entries") else 0
            print(f"{LBL_COLOR}Target:{RST} {TITLE_COLOR}{title} ({count} items){RST}")
        else:
            title = info.get("title") or "Unknown Title"
            print(f"{LBL_COLOR}Title:{RST}  {TITLE_COLOR}{title}{RST}")
    except Exception:
        pass

def progress_hook(d):
    status = d.get('status')
    if status == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes') or 0
        if total > 0:
            percent = downloaded * 100.0 / total
            bar = f"{BAR_COLOR}{_bar(percent)}{RST}"
        else:
            bar = "[Downloading...]"
        sp = (d.get('_speed_str') or '').strip()
        eta = d.get('eta')
        eta_str = f" | ETA: {eta}s" if eta is not None else ""
        print(f"\r{ICON['dl']} {bar} | {sp or '-'}{eta_str}", end="", flush=True)
    elif status == 'finished':
        print(f"\n{ICON['ok']} Downloaded. Post-processing...")

# ---------------------------------
# Filtered logger to hide specific noisy errors
# ---------------------------------
class QuietPathErrorLogger:
    """Suppress 'Unable to open file' / 'Invalid argument' logs from yt-dlp."""
    HIDE_KEYS = ("Unable to open file", "unable to open for writing", "Invalid argument")
    def _hide(self, msg: str) -> bool:
        m = str(msg)
        return any(k.lower() in m.lower() for k in self.HIDE_KEYS)
    def debug(self, msg): pass
    def info(self, msg):
        if not self._hide(msg):
            print(msg)
    def warning(self, msg):
        if not self._hide(msg):
            print(f"⚠️ {msg}")
    def error(self, msg):
        if not self._hide(msg):
            print(f"❌ {msg}", file=sys.stderr)

# ---------------------------------
# Robust download with auto-retry on filename/path errors
# ---------------------------------
def download_with_safe_names(url: str, base_opts: dict, final_format: str, save_path: str):
    """
    Try downloading with progressively safer output templates to avoid
    Windows path errors (Errno 22 Invalid argument) and long filenames.
    """
    templates = [
        "%(title).80B-%(id)s.%(ext)s",
        "%(title).60B-%(id)s.%(ext)s",
        "%(id)s.%(ext)s",
    ]
    last_err = None
    for i, tmpl in enumerate(templates, 1):
        try:
            opts = {
                **base_opts,
                "logger": QuietPathErrorLogger(),
                "restrictfilenames": True,
                "outtmpl_na_placeholder": "NA",
                "outtmpl": os.path.join(save_path, tmpl),
                "format": final_format,
            }
            print(f"{ICON['tip']} Preparing download (safe name level {i}) ...")
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            return True
        except ytdlp_utils.DownloadError as e:
            msg = str(e).lower()
            last_err = e
            # Detect file/path-related errors and retry with safer template
            if "unable to open for writing" in msg or "unable to open file" in msg or "invalid argument" in msg:
                if i < len(templates):
                    print(f"{ICON['warn']} Filename/path issue detected. Retrying with a safer name...")
                    continue
            # Other errors: re-raise
            raise
    # If all templates failed, bubble up the last error
    if last_err:
        raise last_err
    return False

# ---------------------------------
# Main
# ---------------------------------
def main():
    print_banner()

    print("Examples:")
    print("  https://www.facebook.com/watch?v=XXXXXXXX")
    print("  https://fb.watch/XXXX/\n")

    url_in = input(f"{ICON['url']} Enter Facebook video URL: ").strip()
    url = normalize_fb_url(url_in)

    if not is_facebook(url):
        print(f"{ICON['err']} This is not a Facebook URL (facebook.com / fb.watch).")
        sys.exit(2)

    print("\nSelect quality/mode:")
    print("1 - 360p")
    print("2 - 480p")
    print("3 - 720p (common)")
    print("4 - 1080p (requires ffmpeg to merge A/V)")
    print("5 - Best Available")
    print("6 - Audio Only (MP3)")
    print("7 - Video + Subtitles (soft)  [* may not exist on FB]")
    print("8 - Video + Hard-burn Subtitles [* may not exist on FB]")
    choice = input(f"{ICON['prompt']} Your choice: ").strip()

    if choice in {"7", "8"}:
        print(f"{ICON['warn']} Subtitle modes may not be available for Facebook videos. Attempting if present.")

    save_path = get_save_folder()
    requested_fmt = build_format_selector(choice)

    ffmpeg_bin = check_ffmpeg()
    print(f"\nUsing ffmpeg: {PATH_COLOR}{ffmpeg_bin}{RST}")

    print("Getting the Name of the Video...")
    try_print_title(url, ffmpeg_loc=ffmpeg_bin)

    # Common options for FB
    base_opts = {
        "noplaylist": True,
        "ignoreerrors": True,
        "progress_hooks": [progress_hook],
        "windowsfilenames": True,
        "merge_output_format": "mp4",
        "ffmpeg_location": ffmpeg_bin,     # pass full path to avoid warnings
        "quiet": False,
        "no_warnings": True,
        "consoletitle": False,
        "http_headers": {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.5"},
        "geo_bypass": True,
    }

    # Guarantee MP4 output (skip for MP3 and hard-burn)
    if choice not in {"6", "8"}:
        base_opts["recodevideo"] = "mp4"

    # Audio-only (MP3)
    if choice == "6":
        base_opts.update({
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]
        })

    # Soft subtitles (try; may not exist)
    if choice == "7":
        langs_in = input("Enter subtitle language codes (comma-separated, e.g., en,ar,de). Default: en: ").strip()
        langs = [x.strip() for x in langs_in.split(",") if x.strip()] or ["en"]
        base_opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "srt",
            "embedsubtitles": True,
        })

    # Hard-burn subtitles
    if choice == "8":
        langs_in = input("Enter subtitle language codes (comma-separated, e.g., en,ar,de). Default: en: ").strip()
        langs = [x.strip() for x in langs_in.split(",") if x.strip()] or ["en"]
        base_opts.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "srt",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
            "postprocessor_args": {"FFmpegVideoConvertor": ["-vf", "subtitles=%(subtitle_filename)s"]},
        })

    print(f"Save folder: {PATH_COLOR}{save_path}{RST}")

    # -------- Pre-extract with fallbacks to avoid "Cannot parse data" --------
    try:
        with YoutubeDL({**base_opts, "quiet": True}) as ydl_probe:
            info = ydl_probe.extract_info(url, download=False)
    except Exception as e1:
        # Retry with m.facebook.com then mbasic.facebook.com
        tried = [url]
        host = urlparse(url).netloc.lower()
        def swap_host(u, new_host):
            p = urlparse(u)
            return urlunparse((p.scheme or "https", new_host, p.path or "/", p.params, p.query, p.fragment))
        m_url = url if "m.facebook.com" in host else swap_host(url, "m.facebook.com")
        mbasic_url = url if "mbasic.facebook.com" in host else swap_host(url, "mbasic.facebook.com")
        for alt in (m_url, mbasic_url):
            if alt in tried:
                continue
            try:
                with YoutubeDL({**base_opts, "quiet": True}) as ydl_probe2:
                    info = ydl_probe2.extract_info(alt, download=False)
                url = alt
                break
            except Exception as e2:
                tried.append(alt)
        else:
            if looks_private_error(e1):
                print("🔒 The video is private or requires logging in to Facebook. It cannot be downloaded without proper permissions.")
                sys.exit(3)
            print(f"{ICON['err']} Can't parse the Facebook page. (yt-dlp)\n{e1}")
            sys.exit(1)

    # -------- Format decision (avoid 'Requested format is not available') ----
    preferred_h = {"1":360,"2":480,"3":720,"4":1080}.get(choice)
    chosen_id = pick_best_match_format_id(info, preferred_h)
    final_format = chosen_id if chosen_id else requested_fmt
    print(f"Format selector: {final_format}\n")

    # -------- Download with safe filenames & hidden path errors ---------------
    try:
        download_with_safe_names(url, base_opts, final_format, save_path)
        print(f"\n{ICON['ok']} Done!")
        if choice == "8":
            print(f"{ICON['ok']} Subtitles were hard-burned into the video (cannot be toggled off).")
        elif choice == "7":
            print(f"{ICON['ok']} Subtitles were embedded as a soft track and also saved as .srt (if available).")
        elif choice in {"1","2","3","4","5"}:
            print(f"{ICON['ok']} Final output is MP4.")
    except ytdlp_utils.DownloadError as e:
        if looks_private_error(e):
            print("🔒 The video is private or requires logging in to Facebook. It cannot be downloaded without proper permissions.")
            sys.exit(3)
        print(f"\n{ICON['err']} DownloadError:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{ICON['err']} Error during download/conversion:\n{e}")
        print("\nTips:")
        print("- Try another FB URL variant (m.facebook.com / mbasic.facebook.com).")
        print("- Update yt-dlp: pip install -U yt-dlp (script auto-upgrades).")
        print("- 1080p/merging requires ffmpeg (auto-fetched if missing).")
        sys.exit(1)

if __name__ == "__main__":
    main()
