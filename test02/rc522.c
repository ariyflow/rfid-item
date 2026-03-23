#include "rc522.h"
#include <intrins.h>

// 所有局部变量必须加 xdata，防止 data 区溢出 (指导书要求)
#define TRUE  1
#define FALSE 0

// ==========================================
// 底层 SPI 写寄存器
// ==========================================
void WriteRawRC(unsigned char Address, unsigned char value) {
    xdata unsigned char i, ucAddr;
    
    MF522_SCK = 1;        // 空闲状态 (物理低)
    MF522_NSS = 0;        // 片选有效
    
    // 地址格式：[6 位地址][1 位 0(写)][1 位 0]
    ucAddr = ((Address << 1) & 0x7E);
    
    // 发送地址
    for(i = 8; i > 0; i--) {
        // 【关键】MOSI 经过反向器，需要取反输出
        MF522_SI = !((ucAddr & 0x80) == 0x80);
        
        MF522_SCK = 0;    // 产生上升沿 (物理)，RC522 采样
        _nop_();
        ucAddr <<= 1;
        MF522_SCK = 1;    // 恢复空闲
    }
    
    // 发送数据
    for(i = 8; i > 0; i--) {
        // 【关键】MOSI 经过反向器，需要取反输出
        MF522_SI = !((value & 0x80) == 0x80);
        
        MF522_SCK = 0;
        _nop_();
        value <<= 1;
        MF522_SCK = 1;
    }
    
    MF522_NSS = 1;        // 取消片选
    MF522_SCK = 1;        // 恢复空闲
}

// ==========================================
// 底层 SPI 读寄存器
// ==========================================
unsigned char ReadRawRC(unsigned char Address) {
    xdata unsigned char i, ucAddr;
    xdata unsigned char ucResult = 0;
    
    MF522_SCK = 1;        // 空闲状态
    MF522_NSS = 0;        // 片选有效
    
    // 地址格式：[6 位地址][1 位 1(读)][1 位 0]
    ucAddr = ((Address << 1) & 0x7E) | 0x80;
    
    // 发送地址
    for(i = 8; i > 0; i--) {
        MF522_SI = !((ucAddr & 0x80) == 0x80); // 取反
        MF522_SCK = 0;
        _nop_();
        ucAddr <<= 1;
        MF522_SCK = 1;
    }
    
    // 接收数据
    for(i = 8; i > 0; i--) {
        MF522_SCK = 0;    // 产生时钟
        _nop_();
        ucResult <<= 1;
        
        // 【关键】MISO 直连，直接读取，不用取反
        if(MF522_SO) {
            ucResult |= 0x01;
        }
        
        MF522_SCK = 1;    // 恢复空闲
    }
    
    MF522_NSS = 1;
    MF522_SCK = 1;
    
    return ucResult;
}

// ==========================================
// 硬件初始化 (严格匹配指导书 RC522Init)
// ==========================================
void RC522Init() {
    // 1. 配置 P4 口为推挽输出 (驱动反向器)
    P4M1 &= 0xE1;   // 1110 0001
    P4M0 |= 0x1E;   // 0001 1110 (P4.1-P4.4 推挽)
    
    // 2. 配置 P1.0 为高阻输入 (MISO)
    P1M1 |= 0x01;
    P1M0 &= 0xFE;
    
    // 3. 配置 P1.1 为推挽输出 (NSS)
    P1M1 &= 0xFD;
    P1M0 |= 0x02;
    
    // 4. 初始电平状态
    MF522_NSS = 1;      // 未选中
    MF522_SCK = 1;      // 空闲 (物理低)
    MF522_SI  = 1;      // 空闲 (物理低)
    MF522_SO  = 0;      // 输入无关
    
    // 5. 设置 RC522 通信模式 (SPI)
    // 指导书：EA=1, IIC=0 表示 SPI (因有反向器，MCU 输出相反)
    MF522_EA  = 0;      // 物理 1
    MF522_IIC = 1;      // 物理 0 (SPI 模式)
    
    // 6. 软复位
    WriteRawRC(CommandReg, 0x0F); // SoftReset
}

// ==========================================
// 检查版本寄存器
// ==========================================
unsigned char CheckVersion() {
    return ReadRawRC(VersionReg); // 正常应返回 0x91 或 0x92
}