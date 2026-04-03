import logging
import os

from .config import Config
from .ha_client import HAClient
from .s3_client import S3Client
from .coordinator import Coordinator
from .scheduler import Scheduler
from .server import create_app
from .log_buffer import LogBuffer


def setup_logging(log_buffer: LogBuffer, level: str = "INFO"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(handler)
    root.addHandler(log_buffer)


def main():
    log_buffer = LogBuffer()
    config = Config.load()
    setup_logging(log_buffer, getattr(config, "log_level", "INFO"))

    logger = logging.getLogger(__name__)
    logger.info("S3 Backup starting up")

    ha = HAClient(config)
    s3 = S3Client(config)
    coordinator = Coordinator(config, ha, s3)

    Scheduler(coordinator).start()

    flask_app = create_app(coordinator, log_buffer)

    port = int(os.environ.get("INGRESS_PORT", 8099))
    logger.info("Starting Flask on 0.0.0.0:%d", port)
    flask_app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
