from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "9000"))
    api_port: int = int(os.getenv("API_PORT", "8000"))
    auth_token: str = os.getenv("AUTH_TOKEN", "")
    network_interface: str = os.getenv("NETWORK_INTERFACE", "eth0")


settings = Settings()
