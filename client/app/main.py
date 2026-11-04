import logging

from app.application.demo_runner import DemoRunner
from app.config.settings import ClientSettings
from app.infrastructure.server_client import ServerControlClient
from app.infrastructure.traffic_generator import TrafficGenerator


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = ClientSettings.from_environment()
    runner = DemoRunner(
        server_client=ServerControlClient(settings),
        traffic_generator=TrafficGenerator(settings),
    )
    runner.run_once()
    runner.keep_alive()


if __name__ == "__main__":
    main()
