# network_scanner/main.py
# !/usr/bin/env python3
"""
网络扫描工具主入口
用法:
  python -m network_scanner [--gui] [CLI参数...]
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="网络扫描工具",
        epilog="使用 --help 查看命令行模式帮助或 --gui 启动图形界面"
    )
    parser.add_argument('--gui', action='store_true', help="启动图形界面")

    # 分离GUI参数和其他参数
    args, remaining_args = parser.parse_known_args()

    if args.gui:
        from network_scanner.gui import run_gui
        run_gui()
    else:
        from network_scanner.cli import run_cli
        # 将剩余参数传递给CLI
        sys.argv = [sys.argv[0]] + remaining_args
        run_cli()


if __name__ == "__main__":
    main()