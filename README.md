## 网络扫描工具

一、**实验项目名称**

基于Python的网络扫描工具开发

 

二、**实验目的**

1. 掌握Python在网络安全领域的工具开发方法
2. 理解常见安全工具的实现原理与技术
3. 提升模块化开发、异常处理和文档编写能力
4. 培养合法合规的安全开发意识

 

**三、实验任务**

1. 核心功能：

 \- 支持IP范围扫描（如192.168.1.1-254）

 \- 实现TCP SYN端口扫描

 \- 识别端口对应服务类型（Banner抓取）

 \- 输出CSV格式扫描报告

2. 扩展要求：

 \- 添加多线程加速功能

 \- 实现主机存活探测（ICMP/Ping）

3. 时间安排：

| ***\*序号\**** | ***\*任务\****         | ***\*时间\**** |
| -------------- | ---------------------- | -------------- |
| 1              | 需求分析、技术方案设计 | 4.17           |
| 2              | 核心功能开发与单元测试 | 4.18-4.20      |
| 3              | 系统集成与压力测试     | 4.21           |
| 4              | 文档编写与成果提交     | 4.22           |

 

 

**四、主要仪器设备及耗材**

pycharm、kali（2024.1）、Metasploitable2靶机

Python版本：3.12

kali版本具体信息：

![img](./../../TyporaWorkSpace/img/wps2-1745375061022-31.jpg)![img](./../../TyporaWorkSpace/img/wps3-1745375061021-2.jpg) 

 

五、**工具设计原理**

1. 主机发现模块

ICMP Echo请求(Ping)：发送ICMP Echo请求包，等待响应判断主机是否存活。

实现方式：使用Python的socket库构造ICMP包，结合了ARP请求作为局域网内的补充探测。

2. TCP SYN扫描

原理：发送TCP SYN包到目标端口，根据响应判断端口状态。若显示SYN-ACK则表明端口开放；若显示RST则表示端口关闭；若无响应则SYN包可能被过滤。

实现：使用原始socket构造TCP包，需要root权限(在Windows上测试需要管理员权限)

3. 服务识别

Banner抓取：对开放端口建立完整TCP连接，读取服务返回的初始信息。

实现：使用socket建立连接后recv()数据。

4. 多线程处理

设计：使用线程池(ThreadPoolExecutor)管理扫描任务。

注意：控制线程数量避免过度消耗资源；共享数据需要线程安全处理。

5. CSV报告

表格表项设计：IP地址, 端口号, 协议, 服务名称, 状态Banner, 信息。

实现：Python内置csv模块。

6. 测试方案

攻击机：kali（192.168.157.129，NAT模式）

靶机：Metasploitable（192.168.127.130，NAT模式）

主机：VMnet8（192.168.157.1）、WLAN（10.210.21.250）

过程：先测试单个IP的主机发现，然后测试单个主机的端口扫描，最后测试整个IP范围的扫描，验证CSV报告格式和内容。

 

六、**核心代码流程图**

![img](./../../TyporaWorkSpace/img/wps4-1745375061021-5.jpg)           ![img](./../../TyporaWorkSpace/img/wps5-1745375061021-3.jpg)

​                              图1 总流程图                                                     图2 主机发现流程图

 

 

![img](./../../TyporaWorkSpace/img/wps6-1745375061021-4.jpg)       ![img](./../../TyporaWorkSpace/img/wps7-1745375061021-7.jpg)

​                            图3 端口扫描流程图                                    图4 服务识别流程图

<img src="./../../TyporaWorkSpace/img/wps8-1745375061021-6.jpg" alt="img" style="zoom:80%;" />               ![img](./../../TyporaWorkSpace/img/wps9-1745375061022-32.jpg)

​                       图5 报告生成流程图                                                                     图6 项目目录

 

七、**测试用例与结果分析**

将Python项目文件夹通过共享文件夹的形式传入kali，将network_scanner移动至/Scanner目录下。

1. 命令行测试：

![img](./../../TyporaWorkSpace/img/wps10-1745375061021-8.jpg) 

在kali中运行相应命令，格式为：

usage: __main__.py [-h] [-p PORTS] [-t THREADS] [-T TIMEOUT] [--no-arp] [--scan-type {syn,connect}] [-o OUTPUT] [-v] target

其中，-v是开启DEBUG调试。

注意：每次实验前重启Metasploitable恢复初始状态，命令为VBoxManage controlvm "Metasploitable" reset

①　基础功能验证（靶机、常用端口、低线程数、connect）：

python3.12 -m network_scanner 192.168.157.130 -p 22,80 --scan-type connect -t 1 -o exp1.csv -v![img](./../../TyporaWorkSpace/img/wps11-1745375061021-9.jpg)

![img](./../../TyporaWorkSpace/img/wps12-1745375061021-11.jpg) 

表格中的表项分别是目的ip、端口、服务协议、状态、服务名称、banner信息

②　SYN扫描效率测试（靶机、较多端口、低线程数、SYN）：

python3.12 -m network_scanner 192.168.157.130 -p 1-1024 --scan-type syn -t 50

-o exp2.csv -v

![img](./../../TyporaWorkSpace/img/wps13-1745375061021-10.jpg) 

![img](./../../TyporaWorkSpace/img/wps14-1745375061021-12.jpg) 

可以看到，靶机的一些端口名字设置成了具有特殊含义的句子

③　多主机扫描稳定性（多主机、no--arp、其他都是默认）：

python3.12 -m network_scanner 192.168.157.128-135 --no-arp -o exp3.csv

![img](./../../TyporaWorkSpace/img/wps15-1745375061021-13.jpg) 

![img](./../../TyporaWorkSpace/img/wps16-1745375061021-14.jpg)python3.12 -m network_scanner 192.168.157.128-135 -p 21,22,80,443 -t 20 -o exp4.csv

![img](./../../TyporaWorkSpace/img/wps17-1745375061021-15.jpg) 

![img](./../../TyporaWorkSpace/img/wps18-1745375061021-16.jpg) 

④　高线程压力测试（靶机ip、多端口、高线程、syn）：

python3.12 -m network_scanner 192.168.157.130 -p 8000-9000 --scan-type syn -t 100 -o exp5.csv

![img](./../../TyporaWorkSpace/img/wps19-1745375061021-17.jpg) 

![img](./../../TyporaWorkSpace/img/wps20-1745375061021-18.jpg) 

⑤　真实网络设备扫描可行性（本机ip）：

python3.12 -m network_scanner 192.168.157.1 -p 80,443 -t 10 -o exp6.csv -v

![img](./../../TyporaWorkSpace/img/wps21-1745375061021-20.jpg) 

以上的五个测试均成功扫描了目标ip的目的端口，并输出了扫描结果表格exp1-6.csv，可以使用-v来控制是否在命令行中显示日志。

 

2. GUI界面测试：

在kali中的/Scanner文件夹中运行python3.12 -m network_scanner.main --gui，进行GUI界面测试。

网络扫描工具功能：设置扫描目标ip/端口/扫描类型/线程数/扫描超时时间、开始/停止扫描、保存报告、生成扫描日志、汇总扫描结果（包括ip、端口、服务、banner信息）。

①　首先扫描攻击机与靶机所在网段的所有ip的常用端口，进行综合扫描测试（192.168.157.1-255,20-25/80/443，线程数=100，connect扫描）：

![img](./../../TyporaWorkSpace/img/wps22-1745375061021-19.jpg) 

可以看到，扫描日志中记录了工具成功识别到存活主机，并根据扫描到的端口成功识别到了各种服务，最终汇总在扫描结果的表格中。其中192.168.157.1是本机vmnet8的ip地址，192.168.157.130是靶机metasploitable的ip地址。

点击保存报告，选择保存路径。![img](./../../TyporaWorkSpace/img/wps23-1745375061021-21.jpg)

![img](./../../TyporaWorkSpace/img/wps24-1745375061021-22.jpg) 

![img](./../../TyporaWorkSpace/img/wps25-1745375061021-24.jpg) 

并且在关闭该GUI界面后，在kali的该扫描工具的根目录中出现了.log日志文件：

![img](./../../TyporaWorkSpace/img/wps26-1745375061021-23.jpg) 

（这之前有多次测试）

![img](./../../TyporaWorkSpace/img/wps27-1745375061021-25.jpg) 

这是因为在该环境下，192.168.157.1-255中只有vmnet8、攻击机、靶机。

②　根据网络扫描工具中设置的默认ip、端口、扫描类型、线程数进行扫描（192.168.1.1-10,20/80/443，线程数=100，SYN扫描）：

![img](./../../TyporaWorkSpace/img/wps28-1745375061022-26.jpg) 

因为这个ip段内本身就不存在主机。

③　对靶机进行常用端口扫描（192.168.157.130,20/80/443/,线程数=1，connect扫描），进行基础测试：

![img](./../../TyporaWorkSpace/img/wps29-1745375061022-27.jpg) 

![img](./../../TyporaWorkSpace/img/wps30-1745375061022-28.jpg) 

④　对靶机进行线程数较高的扫描，进行高压力线程测试（192.168.157.130,8000-9000，线程数=200，SYN）：

![img](./../../TyporaWorkSpace/img/wps31-1745375061022-29.jpg) 

⑤　对多个主机多个端口进行扫描（192.168.157.100-192.168.157.132，21/22/80/443/520，线程数=10，connect扫描），进行多主机多端口测试：

![img](./../../TyporaWorkSpace/img/wps32-1745375061022-30.jpg) 

以上五个GUI测试均成功扫描了目标ip的目的端口，并在图形化界面中显示出了扫描日志与扫描结果，也可以保存扫描报告至指定路径，报告格式与命令行输出报告格式相同。

 

八、**改进方向与安全性声明**

（一）改进方向：

1. 功能增强

UDP扫描支持：当前仅支持TCP SYN/Connect扫描，可扩展UDP端口扫描（如DNS、SNMP服务探测）。

分布式扫描：通过多节点协作加速大规模网络扫描（如Celery任务队列）。

2. 性能优化

动态线程调整：设计动态线程调整方法，根据网络延迟自动优化线程数（避免资源耗尽或扫描超时）。

结果缓存：设计自动缓存结果方法，对重复扫描的IP/端口启用缓存机制，减少冗余请求，加快扫描速度。

3. 用户体验

交互式报告：生成HTML报告支持结果筛选、排序和可视化图表（如开放端口分布）。

进度显示：在CLI/GUI中添加实时进度条（tqdm库）。

4. 安全性加固

权限隔离：非必要功能（如主机发现）默认以非root权限运行，仅SYN扫描时请求提权。

5. 代码维护性

日志分级存储：分离调试日志与结果日志，便于问题追踪。

（二）安全性声明：

本工具仅限用于 授权测试 和 教学研究，禁止对未授权网络或设备进行扫描；使用者需遵守《网络安全法》及相关法律法规，擅自扫描他人网络可能构成违法行为。SYN扫描：可能触发目标主机的防御机制（如防火墙日志告警），需获得明确授权；高线程扫描：可能导致网络拥塞或目标服务拒绝响应，建议控制线程数（-t参数）。扫描结果（如Banner信息）可能包含敏感数据，需妥善存储和传输，避免泄露。默认日志文件应定期清理或加密保存。

开发者不对工具的滥用行为负责，使用者需自行承担因违规操作导致的法律后果。
