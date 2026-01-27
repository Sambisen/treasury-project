"""
File watcher module for robust Excel file change detection.

Uses watchdog for OS-level file monitoring combined with MD5 hash
verification for bulletproof change detection.
"""
import hashlib
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from config import get_logger

log = get_logger("file_watcher")

# Try to import watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    log.warning("watchdog not installed - falling back to polling mode")


def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Compute MD5 hash of file contents.

    Returns None if file doesn't exist or can't be read.
    """
    try:
        if not file_path.exists():
            return None

        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError) as e:
        log.warning(f"Could not hash file {file_path}: {e}")
        return None


class ExcelFileHandler(FileSystemEventHandler):
    """Watchdog event handler for Excel files."""

    def __init__(self, watcher: 'FileWatcher'):
        super().__init__()
        self.watcher = watcher

    def on_modified(self, event):
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        if src_path.suffix.lower() in ('.xlsx', '.xlsm', '.xls'):
            log.info(f"[FileWatcher] Detected modification: {src_path.name}")
            self.watcher._on_file_event(src_path)

    def on_created(self, event):
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        if src_path.suffix.lower() in ('.xlsx', '.xlsm', '.xls'):
            log.info(f"[FileWatcher] Detected creation: {src_path.name}")
            self.watcher._on_file_event(src_path)


class FileWatcher:
    """
    Robust file watcher with multiple detection strategies.

    Primary: watchdog (OS-level inotify/FSEvents/ReadDirectoryChangesW)
    Fallback: Polling with MD5 hash comparison

    Always verifies changes with MD5 hash to avoid false positives.
    """

    def __init__(
        self,
        on_change_callback: Optional[Callable[[Path], None]] = None,
        debounce_seconds: float = 1.0,
        poll_interval_seconds: float = 5.0,
    ):
        """
        Initialize FileWatcher.

        Args:
            on_change_callback: Function called when file changes (receives Path)
            debounce_seconds: Minimum time between change notifications
            poll_interval_seconds: Interval for fallback polling (if watchdog unavailable)
        """
        self._callback = on_change_callback
        self._debounce_sec = debounce_seconds
        self._poll_interval = poll_interval_seconds

        # Tracked files: path -> {"hash": str, "mtime": float, "size": int}
        self._tracked_files: dict[Path, dict] = {}
        self._lock = threading.Lock()

        # Debounce state
        self._last_notification: dict[Path, float] = {}

        # Watchdog observer
        self._observer: Optional[Observer] = None
        self._watched_dirs: set[Path] = set()

        # Polling fallback
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_stop_event = threading.Event()

        self._started = False

    def watch_file(self, file_path: Path) -> bool:
        """
        Start watching a specific file for changes.

        Args:
            file_path: Path to the file to watch

        Returns:
            True if watching started successfully
        """
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            log.warning(f"[FileWatcher] Cannot watch non-existent file: {file_path}")
            return False

        with self._lock:
            # Compute initial hash and metadata
            file_hash = compute_file_hash(file_path)
            try:
                stat = file_path.stat()
                metadata = {
                    "hash": file_hash,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
            except OSError as e:
                log.error(f"[FileWatcher] Cannot stat file {file_path}: {e}")
                return False

            self._tracked_files[file_path] = metadata
            log.info(f"[FileWatcher] Now watching: {file_path.name} (hash={file_hash[:8]}...)")

            # Set up watchdog for the parent directory
            parent_dir = file_path.parent
            if WATCHDOG_AVAILABLE and parent_dir not in self._watched_dirs:
                self._setup_watchdog(parent_dir)

        return True

    def unwatch_file(self, file_path: Path):
        """Stop watching a specific file."""
        file_path = Path(file_path).resolve()

        with self._lock:
            if file_path in self._tracked_files:
                del self._tracked_files[file_path]
                log.info(f"[FileWatcher] Stopped watching: {file_path.name}")

    def _setup_watchdog(self, directory: Path):
        """Set up watchdog observer for a directory."""
        if not WATCHDOG_AVAILABLE:
            return

        if self._observer is None:
            self._observer = Observer()
            self._observer.start()
            log.info("[FileWatcher] Watchdog observer started")

        handler = ExcelFileHandler(self)
        self._observer.schedule(handler, str(directory), recursive=False)
        self._watched_dirs.add(directory)
        log.info(f"[FileWatcher] Watchdog monitoring: {directory}")

    def _on_file_event(self, file_path: Path):
        """Handle file system event from watchdog."""
        file_path = file_path.resolve()

        with self._lock:
            if file_path not in self._tracked_files:
                # Not a file we're tracking
                return

            # Check debounce
            now = time.time()
            last_notif = self._last_notification.get(file_path, 0)
            if now - last_notif < self._debounce_sec:
                log.debug(f"[FileWatcher] Debouncing event for {file_path.name}")
                return

            # Verify with MD5 hash that content actually changed
            old_hash = self._tracked_files[file_path].get("hash")

            # Small delay to let file writes complete
            time.sleep(0.2)

            new_hash = compute_file_hash(file_path)

            if new_hash is None:
                log.warning(f"[FileWatcher] Could not hash {file_path.name} - file may be locked")
                return

            if new_hash == old_hash:
                log.debug(f"[FileWatcher] Hash unchanged for {file_path.name} - ignoring event")
                return

            # Content actually changed!
            log.info(f"[FileWatcher] CONTENT CHANGED: {file_path.name}")
            log.info(f"[FileWatcher]   Old hash: {old_hash[:8] if old_hash else 'None'}...")
            log.info(f"[FileWatcher]   New hash: {new_hash[:8]}...")

            # Update stored metadata
            try:
                stat = file_path.stat()
                self._tracked_files[file_path] = {
                    "hash": new_hash,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
            except OSError:
                self._tracked_files[file_path]["hash"] = new_hash

            self._last_notification[file_path] = now

        # Call callback outside lock
        if self._callback:
            try:
                self._callback(file_path)
            except Exception as e:
                log.error(f"[FileWatcher] Callback error: {e}")

    def start(self):
        """Start the file watcher."""
        if self._started:
            return

        self._started = True

        # Start polling thread as fallback/supplement
        self._poll_stop_event.clear()
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        log.info(f"[FileWatcher] Started (watchdog={'enabled' if WATCHDOG_AVAILABLE else 'disabled'})")

    def stop(self):
        """Stop the file watcher."""
        if not self._started:
            return

        self._started = False

        # Stop polling
        self._poll_stop_event.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2.0)

        # Stop watchdog
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None

        log.info("[FileWatcher] Stopped")

    def _poll_loop(self):
        """Fallback polling loop for change detection."""
        log.info(f"[FileWatcher] Polling loop started (interval={self._poll_interval}s)")

        while not self._poll_stop_event.is_set():
            self._poll_stop_event.wait(self._poll_interval)

            if self._poll_stop_event.is_set():
                break

            self._check_all_files()

    def _check_all_files(self):
        """Check all tracked files for changes (polling mode)."""
        with self._lock:
            files_to_check = list(self._tracked_files.items())

        for file_path, metadata in files_to_check:
            if not file_path.exists():
                continue

            try:
                stat = file_path.stat()

                # Quick check: mtime or size changed?
                if stat.st_mtime == metadata["mtime"] and stat.st_size == metadata["size"]:
                    continue

                # Something changed - verify with hash
                log.debug(f"[FileWatcher] Metadata changed for {file_path.name}, checking hash...")
                self._on_file_event(file_path)

            except OSError:
                continue

    def check_now(self, file_path: Optional[Path] = None) -> bool:
        """
        Manually check for changes immediately.

        Args:
            file_path: Specific file to check, or None for all files

        Returns:
            True if any changes were detected
        """
        changed = False

        with self._lock:
            if file_path:
                files_to_check = [(file_path.resolve(), self._tracked_files.get(file_path.resolve(), {}))]
            else:
                files_to_check = list(self._tracked_files.items())

        for fp, metadata in files_to_check:
            if not fp.exists():
                continue

            old_hash = metadata.get("hash")
            new_hash = compute_file_hash(fp)

            if new_hash and new_hash != old_hash:
                log.info(f"[FileWatcher] check_now() found change in {fp.name}")
                changed = True
                self._on_file_event(fp)

        return changed

    def get_current_hash(self, file_path: Path) -> Optional[str]:
        """Get the currently stored hash for a watched file."""
        file_path = file_path.resolve()
        with self._lock:
            metadata = self._tracked_files.get(file_path, {})
            return metadata.get("hash")

    def force_rehash(self, file_path: Path) -> Optional[str]:
        """Force recompute and store hash for a file."""
        file_path = file_path.resolve()
        new_hash = compute_file_hash(file_path)

        if new_hash:
            with self._lock:
                if file_path in self._tracked_files:
                    self._tracked_files[file_path]["hash"] = new_hash
                    try:
                        stat = file_path.stat()
                        self._tracked_files[file_path]["mtime"] = stat.st_mtime
                        self._tracked_files[file_path]["size"] = stat.st_size
                    except OSError:
                        pass

        return new_hash
