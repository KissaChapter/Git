# network_scanner/__init__.py
"""
网络扫描工具包
提供以下功能：
- 主机发现(ICMP/ARP)
- 端口扫描(TCP SYN/Connect)
- 服务识别(Banner抓取)
- 报告生成(CSV格式)
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# 暴露主要接口
from .core.scanner import NetworkScanner
from .cli.cli_interface import run_cli
from .gui.gui_interface import run_gui

__all__ = ['NetworkScanner', 'run_cli', 'run_gui']