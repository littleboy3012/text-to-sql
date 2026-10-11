"""
config.py
Configuration loader for environment variables and default application settings.
"""

import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv(override=True)

class Config:
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
    SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b")
    
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "retail_analytics_db")
