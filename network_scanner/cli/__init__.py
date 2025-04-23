# network_scanner/cli/__init__.py
"""
网络扫描器命令行界面

提供命令行参数解析和扫描执行功能
"""

from .cli_interface import parse_arguments, run_cli

__all__ = ['parse_arguments', 'run_cli']