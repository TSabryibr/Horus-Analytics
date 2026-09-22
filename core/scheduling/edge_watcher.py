"""
EDGE PIPELINE FILE WATCHER
==========================
Watches directory for Edge Pipeline validation YAML tickets and triggers ingestion.
"""

import threading
from utils.logger import setup_logger

logger = setup_logger("horus.scheduling.edge_watcher")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False
    logger.warning("[Scheduler] Watchdog library not installed. Edge pipeline watcher will not function.")


class EdgePipelineHandler(FileSystemEventHandler if _WATCHDOG_AVAILABLE else object):
    def __init__(self, parser):
        self.parser = parser
        super().__init__()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.yaml'):
            logger.info(f"[EdgeWatcher] New ticket detected: {event.src_path}")
            self.parser.process_ticket(event.src_path)

    def on_modified(self, event):
        pass


def start_edge_pipeline_watcher():
    if not _WATCHDOG_AVAILABLE:
        return None

    try:
        from core.metrics_parser import MetricsParser
        parser = MetricsParser(
            watch_dir="reports/edge_pipeline/validation",
            processed_dir="reports/edge_pipeline/processed"
        )

        for existing_file in parser.watch_dir.glob("*.yaml"):
            parser.process_ticket(existing_file)

        event_handler = EdgePipelineHandler(parser)
        observer = Observer()
        observer.schedule(event_handler, path=str(parser.watch_dir), recursive=False)

        observer_thread = threading.Thread(target=observer.start, daemon=True, name="EdgePipelineWatcher")
        observer_thread.start()

        logger.info(f"[Scheduler] Edge Pipeline Watcher started on {parser.watch_dir}")
        return observer
    except Exception as e:
        logger.error(f"[Scheduler] Failed to start Edge Pipeline Watcher: {e}", exc_info=True)
        return None
