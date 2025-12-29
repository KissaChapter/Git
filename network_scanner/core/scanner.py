import ipaddress
import threading
import subprocess
import platform
import logging
import socket
import csv
from datetime import datetime
from scapy.layers.l2 import ARP, Ether
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import srp, sr1
from concurrent.futures import ThreadPoolExecutor

# 定义网络端口扫描类
class NetworkScanner:
    def __init__(self, timeout=2, threads=100, log_level=logging.INFO):
        """
        初始化网络扫描器
        :param timeout: 超时时间(秒)
        :param threads: 线程数量
        :param log_level: 日志级别
        """
        self.timeout = timeout
        self.max_threads = threads
        self.scan_results = []
        self.lock = threading.Lock()

        # 初始化日志系统
        self.logger = logging.getLogger('NetworkScanner')
        self.logger.setLevel(log_level)

        # 创建控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        # 创建文件处理器
        log_filename = f"network_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_filename)
        fh.setLevel(log_level)

        # 创建日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # 添加处理器到logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

        self.logger.info("网络扫描器初始化完成")

    def host_discovery(self, ip_range, use_arp=True):
        """
        主机发现模块
        :param ip_range: IP范围字符串，如 "192.168.1.1-254" 或 "192.168.1.0/24"
        :param use_arp: 是否使用ARP扫描(仅局域网有效)
        :return: 存活主机列表
        """
        active_hosts = []

        try:
            self.logger.info(f"开始主机发现扫描: {ip_range}")

            # 解析IP范围
            ip_list = self._parse_ip_range(ip_range)

            # 检查是否为私有地址范围（仅检查第一个IP）
            first_ip = ip_list[0] if ip_list else None
            if use_arp and first_ip:
                try:
                    is_private = ipaddress.ip_address(first_ip.split('-')[0]).is_private
                    if is_private:
                        # 如果是私有地址且使用ARP扫描，转换为CIDR表示法
                        network = ipaddress.IPv4Network(
                            first_ip + '/' + str(ipaddress.IPv4Network(first_ip + '/24').prefixlen), strict=False)
                        active_hosts = self._arp_scan(str(network))
                        self.logger.info(f"ARP扫描完成，发现 {len(active_hosts)} 台活跃主机")
                        return active_hosts
                except ValueError:
                    pass  # 如果无法解析为IP地址，继续使用Ping扫描

            # 使用多线程Ping扫描
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                results = executor.map(self._ping_host, ip_list)
                active_hosts = [ip for ip, alive in zip(ip_list, results) if alive]

            self.logger.info(f"主机发现完成，共发现 {len(active_hosts)} 台活跃主机")
            return active_hosts

        except Exception as e:
            self.logger.error(f"主机发现过程中发生异常: {str(e)}", exc_info=True)
            return []

    def port_scan(self, target_ips, ports='1-1024', scan_type='syn'):
        """
        端口扫描模块
        :param target_ips: 目标IP或IP列表
        :param ports: 端口范围，如 "80,443" 或 "1-1024"
        :param scan_type: 扫描类型 ('syn' 或 'connect')
        :return: 扫描结果列表
        """
        try:
            if isinstance(target_ips, str):
                target_ips = [target_ips]

            port_list = self._parse_port_range(ports)
            self.logger.info(f"开始端口扫描: {len(target_ips)} 主机, {len(port_list)} 端口, 类型: {scan_type}")

            self.scan_results = []
            tasks = []

            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                for ip in target_ips:
                    for port in port_list:
                        if scan_type.lower() == 'syn':
                            tasks.append(executor.submit(self._syn_scan, ip, port))
                        else:
                            tasks.append(executor.submit(self._connect_scan, ip, port))

                for task in tasks:
                    try:
                        task.result()
                    except Exception as e:
                        self.logger.error(f"端口扫描任务异常: {str(e)}", exc_info=True)

            self.logger.info(f"端口扫描完成，共发现 {len(self.scan_results)} 个开放端口")
            return self.scan_results

        except Exception as e:
            self.logger.error(f"端口扫描过程中发生异常: {str(e)}", exc_info=True)
            return []

    def service_scan(self, scan_results=None):
        """
        服务识别模块
        :param scan_results: 扫描结果列表(如果不提供则使用上次扫描结果)
        :return: 包含服务信息的结果列表
        """
        try:
            if scan_results is None:
                scan_results = self.scan_results

            self.logger.info(f"开始服务识别扫描: {len(scan_results)} 个开放端口")

            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                results = list(executor.map(self._get_service_info, scan_results))

            self.logger.info("服务识别扫描完成")
            return results

        except Exception as e:
            self.logger.error(f"服务识别过程中发生异常: {str(e)}", exc_info=True)
            return []

    def generate_report(self, results, filename='scan_report.csv'):
        """
        生成CSV报告
        :param results: 扫描结果列表
        :param filename: 报告文件名
        """
        try:
            self.logger.info(f"生成扫描报告: {filename}")

            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['IP', 'Port', 'Protocol', 'Status', 'Service', 'Banner']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for result in results:
                    writer.writerow({
                        'IP': result['ip'],
                        'Port': result['port'],
                        'Protocol': result.get('protocol', 'tcp'),
                        'Status': result.get('status', 'open'),
                        'Service': result.get('service', 'unknown'),
                        'Banner': result.get('banner', '')
                    })

            self.logger.info(f"报告已生成: {filename}")

        except Exception as e:
            self.logger.error(f"生成报告过程中发生异常: {str(e)}", exc_info=True)

    # ========== 私有方法 ==========

    def _parse_ip_range(self, ip_range):
        """解析IP范围字符串"""
        try:
            if '-' in ip_range:
                base_ip = ip_range.split('-')[0]
                start, end = base_ip.rsplit('.', 1)[0], ip_range.split('-')[1]
                start_ip = base_ip
                end_ip = f"{start}.{end}"

                start = ipaddress.IPv4Address(start_ip)
                end = ipaddress.IPv4Address(end_ip)
                return [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]
            else:
                return [str(ip) for ip in ipaddress.IPv4Network(ip_range, strict=False)]

        except Exception as e:
            self.logger.error(f"解析IP范围失败: {str(e)}", exc_info=True)
            raise

    def _parse_port_range(self, port_range):
        """解析端口范围字符串"""
        try:
            ports = set()
            for part in port_range.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    ports.update(range(start, end + 1))
                else:
                    ports.add(int(part))
            return sorted(ports)

        except Exception as e:
            self.logger.error(f"解析端口范围失败: {str(e)}", exc_info=True)
            raise

    def _ping_host(self, ip):
        """使用系统ping命令检测主机是否存活"""
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', str(int(self.timeout * 1000)), ip]

            output = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout + 1
            )

            if output.returncode == 0:
                self.logger.debug(f"主机存活: {ip}")
                return True
            return False

        except Exception as e:
            self.logger.warning(f"Ping测试失败({ip}): {str(e)}")
            return False

    def _arp_scan(self, ip_range):
        """使用ARP扫描局域网存活主机"""
        try:
            arp = ARP(pdst=ip_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            result = srp(packet, timeout=self.timeout, verbose=0)[0]

            active_hosts = []
            for sent, received in result:
                active_hosts.append(received.psrc)
                self.logger.debug(f"发现ARP响应: {received.psrc} ({received.hwsrc})")

            return active_hosts

        except Exception as e:
            self.logger.error(f"ARP扫描失败: {str(e)}", exc_info=True)
            return []

    def _syn_scan(self, ip, port):
        """TCP SYN扫描"""
        try:
            self.logger.debug(f"SYN扫描: {ip}:{port}")
            packet = IP(dst=ip) / TCP(dport=port, flags="S")
            response = sr1(packet, timeout=self.timeout, verbose=0)

            if response is None:
                return

            if response.haslayer(TCP):
                if response.getlayer(TCP).flags == 0x12:  # SYN-ACK
                    self.logger.info(f"端口开放: {ip}:{port}")
                    with self.lock:
                        self.scan_results.append({'ip': ip, 'port': port, 'status': 'open'})
                    # 发送RST关闭连接
                    sr1(IP(dst=ip) / TCP(dport=port, flags="R"), timeout=self.timeout, verbose=0)
                elif response.getlayer(TCP).flags == 0x14:  # RST-ACK
                    self.logger.debug(f"端口关闭: {ip}:{port}")

        except Exception as e:
            self.logger.error(f"SYN扫描异常({ip}:{port}): {str(e)}")

    def _connect_scan(self, ip, port):
        """TCP连接扫描"""
        try:
            self.logger.debug(f"连接扫描: {ip}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            result = sock.connect_ex((ip, port))
            if result == 0:
                self.logger.info(f"端口开放: {ip}:{port}")
                with self.lock:
                    self.scan_results.append({'ip': ip, 'port': port, 'status': 'open'})
            else:
                self.logger.debug(f"端口关闭: {ip}:{port}")

            sock.close()

        except Exception as e:
            self.logger.error(f"连接扫描异常({ip}:{port}): {str(e)}")

    def _get_service_info(self, scan_result):
        """获取服务信息"""
        try:
            ip = scan_result['ip']
            port = scan_result['port']

            self.logger.debug(f"获取服务信息: {ip}:{port}")

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            sock.connect((ip, port))

            # 尝试获取banner
            try:
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                scan_result['banner'] = banner
                self.logger.debug(f"获取到banner: {ip}:{port} - {banner[:50]}...")
            except:
                scan_result['banner'] = ''

            # 尝试识别服务
            try:
                service = socket.getservbyport(port, 'tcp')
                scan_result['service'] = service
                self.logger.debug(f"识别服务: {ip}:{port} - {service}")
            except:
                scan_result['service'] = 'unknown'

            sock.close()
            return scan_result

        except Exception as e:
            self.logger.error(f"获取服务信息异常({ip}:{port}): {str(e)}")
            return scan_result