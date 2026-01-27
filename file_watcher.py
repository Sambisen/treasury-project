"""
File watcher module for robust Excel file change detection.

Uses watchdog for OS-level file monitoring combined with MD5 hash
verification for bulletproof change detection.

Handles Excel auto-save by using a "quiet period" - only notifies
after the file has been stable (no changes) for X seconds.
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
            log.debug(f"[FileWatcher] Detected modification: {src_path.name}")
            self.watcher._on_file_event(src_path)

    def on_created(self, event):
        if event.is_directory:
            return

        src_path = Path(event.src_path)
        if src_path.suffix.lower() in ('.xlsx', '.xlsm', '.xls'):
            log.debug(f"[FileWatcher] Detected creation: {src_path.name}")
            self.watcher._on_file_event(src_path)


class FileWatcher:
    """
    Robust file watcher with multiple detection strategies.

    Primary: watchdog (OS-level inotify/FSEvents/ReadDirectoryChangesW)
    Fallback: Polling with MD5 hash comparison

    Handles auto-save by using a "quiet period":
    - Only notifies after file has been stable for X seconds
    - Prevents notification spam during active editing
    - Cooldown prevents multiple notifications within Y seconds
    """

    def __init__(
        self,
        on_change_callback: Optional[Callable[[Path], None]] = None,
        quiet_period_seconds: float = 10.0,
        notification_cooldown_seconds: float = 60.0,
        poll_interval_seconds: float = 5.0,
    ):
        """
        Initialize FileWatcher.

        Args:
            on_change_callback: Function called when file changes (receives Path)
            quiet_period_seconds: Wait this long after last change before notifying
            notification_cooldown_seconds: Minimum time between notifications for same file
            poll_interval_seconds: Interval for fallback polling (if watchdog unavailable)
        """
        self._callback = on_change_callback
        self._quiet_period = quiet_period_seconds
        self._cooldown = notification_cooldown_seconds
        self._poll_interval = poll_interval_seconds

        # Tracked files: path -> {"hash": str, "mtime": float, "size": int}
        self._tracked_files: dict[Path, dict] = {}
        self._lock = threading.Lock()

        # Quiet period state: path -> timestamp of last event
        self._last_event_time: dict[Path, float] = {}
        self._pending_notifications: dict[Path, str] = {}  # path -> hash at time of change

        # Cooldown state: path -> timestamp of last notification
        self._last_notification_time: dict[Path, float] = {}

        # Watchdog observer
        self._observer: Optional[Observer] = None
        self._watched_dirs: set[Path] = set()

        # Background threads
        self._poll_thread: Optional[threading.Thread] = None
        self._quiet_check_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

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
            log.info(f"[FileWatcher] Now watching: {file_path.name} (hash={file_hash[:8] if file_hash else 'None'}...)")

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
        """
        Handle file system event from watchdog.

        Instead of notifying immediately, record the event time and
        let the quiet period checker handle notification.
        """
        file_path = file_path.resolve()

        with self._lock:
            if file_path not in self._tracked_files:
                return

            now = time.time()

            # Record this event time (resets quiet period timer)
            self._last_event_time[file_path] = now

            # Check if content actually changed (quick hash check)
            old_hash = self._tracked_files[file_path].get("hash")

            # Small delay to let file writes complete
            time.sleep(0.1)

            new_hash = compute_file_hash(file_path)

            if new_hash is None:
                log.debug(f"[FileWatcher] Could not hash {file_path.name} - file may be locked")
                return

            if new_hash != old_hash:
                # Content changed - mark as pending
                self._pending_notifications[file_path] = new_hash
                log.debug(f"[FileWatcher] Change detected in {file_path.name}, waiting for quiet period...")

    def _check_quiet_periods(self):
        """
        Background thread that checks if quiet periods have elapsed.

        When a file has been stable (no changes) for quiet_period_seconds,
        and cooldown has passed, trigger the notification.
        """
        log.info(f"[FileWatcher] Quiet period checker started (quiet={self._quiet_period}s, cooldown={self._cooldown}s)")

        while not self._stop_event.is_set():
            self._stop_event.wait(1.0)  # Check every second

            if self._stop_event.is_set():
                break

            now = time.time()
            files_to_notify = []

            with self._lock:
                for file_path, new_hash in list(self._pending_notifications.items()):
                    last_event = self._last_event_time.get(file_path, 0)
                    last_notif = self._last_notification_time.get(file_path, 0)

                    # Check quiet period elapsed
                    quiet_elapsed = now - last_event >= self._quiet_period

                    # Check cooldown elapsed
                    cooldown_elapsed = now - last_notif >= self._cooldown

                    if quiet_elapsed and cooldown_elapsed:
                        # Verify hash is still different from stored
                        old_hash = self._tracked_files.get(file_path, {}).get("hash")

                        if new_hash != old_hash:
                            files_to_notify.append((file_path, new_hash))

                            # Update stored hash
                            if file_path in self._tracked_files:
                                self._tracked_files[file_path]["hash"] = new_hash
                                try:
                                    stat = file_path.stat()
                                    self._tracked_files[file_path]["mtime"] = stat.st_mtime
                                    self._tracked_files[file_path]["size"] = stat.st_size
                                except OSError:
                                    pass

                            # Record notification time
                            self._last_notification_time[file_path] = now

                        # Remove from pending
                        del self._pending_notifications[file_path]

            # Notify outside lock
            for file_path, new_hash in files_to_notify:
                log.info(f"[FileWatcher] STABLE CHANGE DETECTED: {file_path.name}")
                log.info(f"[FileWatcher]   New hash: {new_hash[:8]}...")

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
        self._stop_event.clear()

        # Start quiet period checker thread
        self._quiet_check_thread = threading.Thread(target=self._check_quiet_periods, daemon=True)
        self._quiet_check_thread.start()

        # Start polling thread as fallback/supplement
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        log.info(f"[FileWatcher] Started (watchdog={'enabled' if WATCHDOG_AVAILABLE else 'disabled'}, quiet_period={self._quiet_period}s)")

    def stop(self):
        """Stop the file watcher."""
        if not self._started:
            return

        self._started = False
        self._stop_event.set()

        # Wait for threads
        if self._quiet_check_thread and self._quiet_check_thread.is_alive():
            self._quiet_check_thread.join(timeout=2.0)

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

        while not self._stop_event.is_set():
            self._stop_event.wait(self._poll_interval)

            if self._stop_event.is_set():
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

                # Something changed - trigger event handler
                log.debug(f"[FileWatcher] Polling detected change in {file_path.name}")
                self._on_file_event(file_path)

            except OSError:
                continue

    def check_now(self, file_path: Optional[Path] = None) -> bool:
        """
        Manually check for changes immediately (bypasses quiet period).

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

                # Update hash immediately
                with self._lock:
                    if fp in self._tracked_files:
                        self._tracked_files[fp]["hash"] = new_hash
                        self._last_notification_time[fp] = time.time()

                # Notify
                if self._callback:
                    try:
                        self._callback(fp)
                    except Exception as e:
                        log.error(f"[FileWatcher] Callback error: {e}")

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

    def has_pending_changes(self, file_path: Optional[Path] = None) -> bool:
        """Check if there are pending changes waiting for quiet period."""
        with self._lock:
            if file_path:
                return file_path.resolve() in self._pending_notifications
            return len(self._pending_notifications) > 0
