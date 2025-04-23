# gui/gui_interface.py
# 添加在文件最开头
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from core.scanner import NetworkScanner
import threading
import logging
from io import StringIO
'''参数输入	提供表单控件（输入框、单选按钮、滑块等）替代命令行参数
扫描控制	通过按钮触发扫描，支持开始/停止操作
实时日志	在滚动文本框中显示扫描进度和调试信息（scrolledtext.ScrolledText）
结果展示	用树形表格（ttk.Treeview）直观显示开放的IP、端口、服务及Banner信息
报告导出	支持将结果保存为CSV文件（通过文件对话框选择路径）'''

class ScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网络扫描工具")
        self.root.geometry("800x600")

        # 日志捕获
        self.log_stream = StringIO()
        self.setup_logging()

        # 初始化扫描器
        self.scanner = NetworkScanner(log_level=logging.INFO)
        self.scanning = False

        self.setup_ui()

    def setup_logging(self):
        # 配置日志到StringIO
        handler = logging.StreamHandler(self.log_stream)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        logger = logging.getLogger('NetworkScanner')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="扫描设置", padding="10")
        input_frame.pack(fill=tk.X, pady=5)

        # 目标输入
        ttk.Label(input_frame, text="目标IP范围:").grid(row=0, column=0, sticky=tk.W)
        self.target_entry = ttk.Entry(input_frame, width=30)
        self.target_entry.grid(row=0, column=1, sticky=tk.W)
        self.target_entry.insert(0, "192.168.1.1-10")

        # 端口输入
        ttk.Label(input_frame, text="端口范围:").grid(row=1, column=0, sticky=tk.W)
        self.ports_entry = ttk.Entry(input_frame, width=30)
        self.ports_entry.grid(row=1, column=1, sticky=tk.W)
        self.ports_entry.insert(0, "22,80,443")

        # 扫描类型
        ttk.Label(input_frame, text="扫描类型:").grid(row=2, column=0, sticky=tk.W)
        self.scan_type = tk.StringVar(value="syn")
        ttk.Radiobutton(input_frame, text="SYN扫描", variable=self.scan_type, value="syn").grid(row=2, column=1,
                                                                                                sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Connect扫描", variable=self.scan_type, value="connect").grid(row=2, column=2,
                                                                                                        sticky=tk.W)

        # 高级选项
        ttk.Label(input_frame, text="线程数:").grid(row=3, column=0, sticky=tk.W)
        self.threads_entry = ttk.Spinbox(input_frame, from_=1, to=500, width=5)
        self.threads_entry.grid(row=3, column=1, sticky=tk.W)
        self.threads_entry.set(100)

        ttk.Label(input_frame, text="超时(秒):").grid(row=3, column=2, sticky=tk.W)
        self.timeout_entry = ttk.Spinbox(input_frame, from_=1, to=10, width=5)
        self.timeout_entry.grid(row=3, column=3, sticky=tk.W)
        self.timeout_entry.set(2)

        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.start_button = ttk.Button(button_frame, text="开始扫描", command=self.start_scan)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止扫描", command=self.stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="保存报告", command=self.save_report).pack(side=tk.LEFT, padx=5)

        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="扫描日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 结果表格
        result_frame = ttk.LabelFrame(main_frame, text="扫描结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("ip", "port", "service", "banner")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)

        self.result_tree.heading("ip", text="IP地址")
        self.result_tree.heading("port", text="端口")
        self.result_tree.heading("service", text="服务")
        self.result_tree.heading("banner", text="Banner信息")

        self.result_tree.column("ip", width=120)
        self.result_tree.column("port", width=60)
        self.result_tree.column("service", width=120)
        self.result_tree.column("banner", width=400)

        self.result_tree.pack(fill=tk.BOTH, expand=True)

        # 定期更新日志
        self.update_log()

    def update_log(self):
        # 更新日志显示
        log_content = self.log_stream.getvalue()
        if log_content:
            self.log_text.insert(tk.END, log_content)
            self.log_text.see(tk.END)
            self.log_stream.seek(0)
            self.log_stream.truncate(0)

        # 每500ms检查一次
        self.root.after(500, self.update_log)

    def start_scan(self):
        if self.scanning:
            return

        self.scanning = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        # 获取参数
        target = self.target_entry.get()
        ports = self.ports_entry.get()
        scan_type = self.scan_type.get()
        threads = int(self.threads_entry.get())
        timeout = float(self.timeout_entry.get())

        # 初始化扫描器
        self.scanner = NetworkScanner(
            timeout=timeout,
            threads=threads,
            log_level=logging.DEBUG
        )

        # 在新线程中运行扫描
        scan_thread = threading.Thread(
            target=self.run_scan,
            args=(target, ports, scan_type),
            daemon=True
        )
        scan_thread.start()

    def run_scan(self, target, ports, scan_type):
        try:
            # 1. 主机发现
            targets = self.scanner.host_discovery(target)

            if not targets:
                messagebox.showinfo("扫描完成", "没有发现存活主机")
                return

            # 2. 端口扫描
            scan_results = self.scanner.port_scan(targets, ports=ports, scan_type=scan_type)

            # 3. 服务识别
            service_results = self.scanner.service_scan()

            # 更新结果表格
            for result in service_results:
                self.result_tree.insert("", tk.END, values=(
                    result['ip'],
                    result['port'],
                    result.get('service', 'unknown'),
                    result.get('banner', '')[:100] + "..." if len(result.get('banner', '')) > 100 else result.get(
                        'banner', '')
                ))

            messagebox.showinfo("扫描完成", f"扫描完成，共发现 {len(service_results)} 个开放端口")

        except Exception as e:
            messagebox.showerror("扫描错误", f"发生错误: {str(e)}")
        finally:
            self.scanning = False
            self.root.after(100, lambda: self.start_button.config(state=tk.NORMAL))
            self.root.after(100, lambda: self.stop_button.config(state=tk.DISABLED))

    def stop_scan(self):
        if self.scanning:
            self.scanning = False
            # 这里可以添加扫描停止的逻辑

    def save_report(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="保存扫描报告"
        )

        if filename:
            try:
                # 从表格中获取数据
                results = []
                for item in self.result_tree.get_children():
                    values = self.result_tree.item(item, 'values')
                    results.append({
                        'ip': values[0],
                        'port': values[1],
                        'service': values[2],
                        'banner': values[3]
                    })

                if results:
                    self.scanner.generate_report(results, filename)
                    messagebox.showinfo("保存成功", f"报告已保存到 {filename}")
                else:
                    messagebox.showwarning("无数据", "没有扫描结果可保存")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存报告时出错: {str(e)}")


def run_gui():
    root = tk.Tk()
    app = ScannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()