import logging
import threading
import time

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 3600


class Scheduler:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def start(self):
        t = threading.Thread(target=self._run, daemon=True, name="scheduler")
        t.start()

    def _run(self):
        logger.info("Scheduler started (interval=%ds)", SYNC_INTERVAL_SECONDS)
        self.coordinator.refresh_backups()
        while True:
            time.sleep(SYNC_INTERVAL_SECONDS)
            try:
                if self.coordinator.is_backup_due():
                    logger.info("Scheduled backup triggered")
                    self.coordinator.create_backup()
                self.coordinator.sync()
            except Exception as e:
                logger.error("Scheduler error: %s", e)
