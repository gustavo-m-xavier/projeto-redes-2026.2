import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ClientSettings:
    server_host: str
    server_port: int
    api_port: int
    auth_token: str

    @classmethod
    def from_environment(cls) -> "ClientSettings":
        return cls(
            server_host=os.getenv("SERVER_HOST", "127.0.0.1"),
            server_port=int(os.getenv("SERVER_PORT", "9000")),
            api_port=int(os.getenv("API_PORT", "8000")),
            auth_token=os.getenv("AUTH_TOKEN", ""),
        )
