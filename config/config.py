import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY         = os.getenv("SECRET_KEY", "change-me")
    DEBUG              = os.getenv("APP_DEBUG", "False") == "True"

    MYSQL_HOST         = os.getenv("DB_HOST", "localhost")
    MYSQL_PORT         = int(os.getenv("DB_PORT", 3306))
    MYSQL_DB           = os.getenv("DB_DATABASE", "3IdeaTask")
    MYSQL_USER         = os.getenv("DB_USERNAME", "bwr_user")
    MYSQL_PASSWORD     = os.getenv("DB_PASSWORD", "Root@12345")
    MYSQL_CURSORCLASS  = "DictCursor"
