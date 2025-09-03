import logging
import logging.config
from typing import Optional
from app.core.config import settings

def setup_logging(log_level: Optional[str] = None):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Optional log level to override the default from settings
    """
    # Default log level from settings or INFO if not set
    level = log_level or settings.LOG_LEVEL
    
    # Convert string level to logging constant
    try:
        numeric_level = getattr(logging, level.upper())
    except AttributeError:
        # If the level is not valid, default to INFO
        numeric_level = logging.INFO
        print(f"Invalid log level '{level}', defaulting to INFO")
    
    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': numeric_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': numeric_level,
                'formatter': 'detailed',
                'filename': 'app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': numeric_level,
                'propagate': False
            },
            # Reduce verbosity of SQLAlchemy logs
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.dialects': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.pool': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.orm': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.engine.Engine': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)

def get_logger(name: str):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)