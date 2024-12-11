"""Store the config"""
from datetime import timedelta
import os
import dataclasses


@dataclasses.dataclass
class Config:
    """Load the configuration key SECRET and JWT_SECRET """
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'supersecretjwtkey')
    JWT_ACCESS_TOKEN_EXPIRES = os.getenv(
        'JWT_ACCESS_TOKEN_EXPIRES', timedelta(seconds=int(3600)))
