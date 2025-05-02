"""
Logging configuration for Agentic RAG.

This module provides logging configuration for the Agentic RAG system.
"""

import logging
import logging.config
import os
import json
from typing import Dict, Any, Optional


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        config: Logging configuration dictionary (optional)
    """
    if config is None:
        # Use default configuration
        config = {
            "level": "info",
            "format": "text",
            "output": "console",
            "file_path": "logs/agentic-rag.log"
        }
    
    # Map log level strings to logging constants
    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    log_level = log_level_map.get(
        config.get("level", "info").lower(),
        logging.INFO
    )
    
    # Configure formats
    if config.get("format") == "json":
        log_format = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure handlers
    handlers = []
    
    if config.get("output") in ["console", "both"]:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    
    if config.get("output") in ["file", "both"] and config.get("file_path"):
        # Ensure log directory exists
        log_dir = os.path.dirname(config["file_path"])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(config["file_path"])
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    # Set up loggers for each component
    loggers = {
        "agentic_rag": {"level": log_level},
        "agentic_rag.api": {"level": log_level},
        "agentic_rag.memory": {"level": log_level},
        "agentic_rag.planning": {"level": log_level},
        "agentic_rag.agents": {"level": log_level}
    }
    
    for logger_name, logger_config in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_config["level"])
        
        # Ensure handlers are not duplicated
        if not logger.handlers:
            for handler in handlers:
                logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"agentic_rag.{name}")


def load_logging_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load logging configuration from a file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return config.get("logging", {})
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logging.warning(f"Failed to load logging configuration: {str(e)}")
        return {}