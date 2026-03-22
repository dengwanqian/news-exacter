#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 确保logs目录存在
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 创建日志文件路径
LOG_FILE = os.path.join(LOG_DIR, f"news_exacter_{datetime.now().strftime('%Y%m%d')}.log")

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建日志记录器
def get_logger(name):
    """
    获取日志记录器
    :param name: 日志记录器名称
    :return: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建文件处理器（带轮转）
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# 分类日志记录器
def get_category_logger(category):
    """
    获取分类日志记录器
    :param category: 日志分类
    :return: 配置好的日志记录器
    """
    return get_logger(f"{category}")

# 预定义分类日志记录器
info_logger = get_category_logger("info")
debug_logger = get_category_logger("debug")
error_logger = get_category_logger("error")
warning_logger = get_category_logger("warning")

# 便捷函数
def info(message, category="info"):
    """
    记录信息日志
    :param message: 日志信息
    :param category: 日志分类
    """
    get_category_logger(category).info(message)

def debug(message, category="debug"):
    """
    记录调试日志
    :param message: 日志信息
    :param category: 日志分类
    """
    get_category_logger(category).debug(message)

def error(message, category="error"):
    """
    记录错误日志
    :param message: 日志信息
    :param category: 日志分类
    """
    get_category_logger(category).error(message)

def warning(message, category="warning"):
    """
    记录警告日志
    :param message: 日志信息
    :param category: 日志分类
    """
    get_category_logger(category).warning(message)