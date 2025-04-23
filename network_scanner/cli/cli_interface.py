# cli/cli_interface.py
import argparse
import logging
from core.scanner import NetworkScanner
'''参数解析	使用 argparse 定义命令行参数（如目标IP、端口范围、线程数等）
流程控制	按步骤执行 主机发现 → 端口扫描 → 服务识别 → 生成报告
用户交互	打印扫描进度和结果（如 [1/3] 主机发现...）
异常处理	捕获 KeyboardInterrupt（用户中断）和常规错误，友好提示'''

def parse_arguments():
    parser = argparse.ArgumentParser(description="网络扫描工具")

    # 基本参数
    parser.add_argument('target', help="目标IP范围(如 192.168.1.1-254)")
    parser.add_argument('-p', '--ports', default='1-1024',
                        help="端口范围(默认: 1-1024)")
    parser.add_argument('-t', '--threads', type=int, default=100,
                        help="线程数(默认: 100)")
    parser.add_argument('-T', '--timeout', type=float, default=2.0,
                        help="超时时间(秒)(默认: 2)")

    # 扫描选项
    parser.add_argument('--no-arp', action='store_false', dest='use_arp',
                        help="禁用ARP扫描")
    parser.add_argument('--scan-type', choices=['syn', 'connect'], default='syn',
                        help="扫描类型: syn(默认)或connect")

    # 输出选项
    parser.add_argument('-o', '--output', default='scan_report.csv',
                        help="输出文件名(默认: scan_report.csv)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="详细输出模式")

    return parser.parse_args()


def run_cli():
    args = parse_arguments()

    # 初始化扫描器
    log_level = logging.DEBUG if args.verbose else logging.INFO
    scanner = NetworkScanner(
        timeout=args.timeout,
        threads=args.threads,
        log_level=log_level
    )

    try:
        print("=== 开始网络扫描 ===")

        # 1. 主机发现
        print("\n[1/3] 主机发现...")
        targets = scanner.host_discovery(args.target, use_arp=args.use_arp)
        print(f"发现存活主机: {targets}")

        if not targets:
            print("没有发现存活主机，退出扫描")
            return

        # 2. 端口扫描
        print(f"\n[2/3] 端口扫描({args.scan_type})...")
        scan_results = scanner.port_scan(targets, ports=args.ports, scan_type=args.scan_type)

        # 3. 服务识别
        print("\n[3/3] 服务识别...")
        service_results = scanner.service_scan()

        # 4. 生成报告
        print(f"\n生成报告: {args.output}")
        scanner.generate_report(service_results, args.output)

        print("\n扫描完成!")

    except KeyboardInterrupt:
        print("\n扫描被用户中断")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")


if __name__ == "__main__":
    run_cli()