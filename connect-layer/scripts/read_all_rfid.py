#!/usr/bin/env python3
"""
读取所有RFID存储地址的数据

通信协议：感知层-网络层通信协议
- 读取地址数据（01指令）：发送 aa 55 01 addr 00...00 xx
- 接收数据：aa 55 13 01 addr d1-d16 xx

地址范围：0-63，不包括4*i+3（即3,7,11,15,19,23,27,31,35,39,43,47,51,55,59,63不可用）
可用地址共48个
"""

import serial
import serial.tools.list_ports
import time
import os
import sys
import logging as lg

# 协议常量
FRAME_HEAD = b"\xaa\x55"
CMD_READ = 0x01
FRAME_LEN = 24  # 固定帧长度：包头2 + 指令1 + 地址1 + 数据16 + 补齐3 + 校验1

lg.basicConfig(
    filename="card.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=lg.INFO
)
lg.info("程序开始运行")

def calculate_checksum(data: bytes) -> int:
    """计算偶校验码"""
    checksum = 0
    for b in data:
        checksum ^= b
    return checksum

def bytes_output_format(data: bytes):
    return " ".join(b.to_bytes(1, "big").hex().upper() for b in data)

def build_read_frame(addr: int) -> bytes:
    """构建读取地址的数据帧

    Args:
        addr: RFID存储地址 (0-63)
    Returns:
        24字节的数据帧
    """
    if not (0 <= addr <= 63):
        raise ValueError(f"地址必须在0-63之间，当前值: {addr}")

    # 帧结构：包头2 + 指令1 + 地址1 + 补齐19 + 校验1
    frame = FRAME_HEAD + bytes([CMD_READ, addr]) + b"\x00" * 19
    checksum = calculate_checksum(frame)
    return frame + bytes([checksum])


def parse_response(data: bytes) -> tuple:
    """解析感知层返回的数据帧

    Args:
        data: 原始数据帧
    Returns:
        (addr, content) - 地址和数据内容
    Raises:
        ValueError: 数据格式错误
    """
    if len(data) < 5:
        raise ValueError(f"数据帧太短: {len(data)} 字节")

    if data[:2] != FRAME_HEAD:
        raise ValueError(f"帧头错误: {data[:2].hex()}")

    frame_len = data[2]
    if len(data) != frame_len + 3:  # +3 是因为前面有2字节包头 + 1字节长度
        raise ValueError(f"帧长度不匹配: 声明{FRAME_LEN}, 实际{len(data)}")

    cmd = data[3]
    if cmd != CMD_READ:
        raise ValueError(f"指令错误: 期望01, 实际{cmd:02X}")

    addr = data[4]
    content = data[5:-1]  # 去掉最后一个校验字节

    return addr, content


def get_valid_addresses() -> list:
    """获取所有有效的RFID存储地址

    排除4*i+3的地址
    """
    return [addr for addr in range(64) if addr % 4 != 3]


def find_serial_port() -> str:
    """自动查找串口

    Returns:
        串口设备路径
    Raises:
        RuntimeError: 未找到可用串口
    """
    ports = serial.tools.list_ports.comports()
    usb_ports = [p for p in ports if "USB" in p.hwid]

    if not usb_ports:
        raise RuntimeError("未找到可用串口设备")

    if len(usb_ports) == 1:
        port = usb_ports[0].device
        print(f"自动选择串口: {port}")
        return port

    print("找到多个串口设备:")
    for i, p in enumerate(usb_ports):
        print(f"  [{i}] {p.device} - {p.description}")

    while True:
        try:
            choice = int(input("请选择串口编号: "))
            if 0 <= choice < len(usb_ports):
                return usb_ports[choice].device
            print("无效选择")
        except ValueError:
            print("请输入数字")


def read_all_rfid(serial_port: str, baudrate: int = 9600, timeout: float = 1.0,
                  output_file: str = None, delay: float = 0.1) -> dict:
    """读取所有RFID存储地址的数据

    Args:
        serial_port: 串口设备路径
        baudrate: 波特率，默认9600
        timeout: 读取超时时间（秒）
        output_file: 输出文件路径，None则打印到标准输出
        delay: 每次读取间隔（秒）

    Returns:
        {addr: bytes} - 地址到数据的映射
    """
    results = {}
    valid_addrs = get_valid_addresses()

    try:
        ser = serial.Serial(serial_port, baudrate, timeout=timeout)
        print(f"已打开串口: {serial_port} @ {baudrate}")

        for i, addr in enumerate(valid_addrs):
            # 发送读取请求
            frame = build_read_frame(addr)
            lg.info(f"准备发送数据帧：{bytes_output_format(frame)}")
            ser.write(frame)

            # 等待响应
            time.sleep(delay)

            # 读取响应
            response = ser.read(FRAME_LEN)
            lg.info(f"读取到响应：{bytes_output_format(response)}")

            if len(response) == FRAME_LEN:
                try:
                    recv_addr, content = parse_response(response)
                    results[recv_addr] = content
                    hex_str = " ".join(f"{b:02X}" for b in content)
                    print(f"[{i+1}/{len(valid_addrs)}] 地址 {recv_addr:02X}: {hex_str}")

                    if output_file:
                        with open(output_file, "a") as f:
                            f.write(f"地址 {recv_addr:02X}: {hex_str}\n")
                except ValueError as e:
                    print(f"[{i+1}/{len(valid_addrs)}] 地址 {addr:02X} 解析错误: {e}")
            else:
                print(f"[{i+1}/{len(valid_addrs)}] 地址 {addr:02X} 无响应或响应不完整")

    finally:
        if 'ser' in locals():
            ser.close()
            print("串口已关闭")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="读取所有RFID存储地址的数据")
    parser.add_argument("-p", "--port", help="串口设备路径，如 /dev/ttyUSB0")
    parser.add_argument("-b", "--baudrate", type=int, default=9600, help="波特率，默认9600")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="读取间隔（秒），默认0.1")

    args = parser.parse_args()

    # 确定串口
    if args.port:
        serial_port = args.port
    else:
        serial_port = find_serial_port()

    # 清除输出文件
    if args.output:
        with open(args.output, "w") as f:
            f.write(f"RFID存储数据读取 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"串口: {serial_port} @ {args.baudrate}\n")
            f.write("-" * 60 + "\n")

    print(f"开始读取RFID存储，有效地址 {len(get_valid_addresses())} 个")
    print("-" * 60)

    results = read_all_rfid(
        serial_port,
        baudrate=args.baudrate,
        output_file=args.output,
        delay=args.delay
    )

    print("-" * 60)
    print(f"读取完成: {len(results)}/{len(get_valid_addresses())} 个地址")

    if args.output:
        print(f"数据已保存到: {args.output}")


if __name__ == "__main__":
    main()