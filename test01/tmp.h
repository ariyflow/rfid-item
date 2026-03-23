#include <regx52.H>
#include <intrins.h>

// ==========================================
// 1. 引脚定义 (根据用户提供的硬件映射)
// ==========================================
sbit RC522_MISO = P1^0;   // 0x90, 直连，输入
sbit RC522_NSS  = P1^1;   // 0x91, 直连，输出 (低电平选中)
sbit RC522_SCK  = P4^1;   // 0xC1, 反向器，输出 (1=物理低，0=物理高)
sbit RC522_MOSI = P4^2;   // 0xC2, 反向器，输出 (0=物理高 1, 1=物理低 0)
sbit RC522_RST  = P4^3;   // 0xC3, 反向器，输出 (1=物理低 Reset)
sbit RC522_MODE = P4^4;   // 0xC4, 反向器，输出 (1=物理低 SPI 模式)

sfr P1M1 = 0x91;
sfr P1M0 = 0x92;

// ==========================================
// 2. 基础延时 (用于 SPI 时序稳定)
// ==========================================
// STC15 速度很快，需要少量延时确保 RC522 能跟上
void Delay_us(unsigned int t) {
    while(t--);
}

// ==========================================
// 3. SPI 底层读写 (核心逻辑匹配 HEX 0x1482)
// ==========================================

// 发送一个字节到 RC522
void RC522_SPI_WriteByte(unsigned char dat) {
    unsigned char i;
    for(i = 0; i < 8; i++) {
        // 1. 准备数据 (MOSI)
        // 逻辑 1 -> MCU 输出 0 (经反向器变物理 1)
        // 逻辑 0 -> MCU 输出 1 (经反向器变物理 0)
        if(dat & 0x80) 
            RC522_MOSI = 0; 
        else 
            RC522_MOSI = 1;
        
        dat <<= 1;
        
        // 2. 产生时钟脉冲 (SCK)
        // 空闲状态 MCU=1 (物理 0)
        // 脉冲状态 MCU=0 (物理 1) -> 上升沿/采样
        RC522_SCK = 0;      // 拉低 MCU，物理变高 (Clock High)
        _nop_();            // 保持高电平
        RC522_SCK = 1;      // 拉高 MCU，物理变低 (Clock Low)
    }
}

// 从 RC522 读取一个字节
unsigned char RC522_SPI_ReadByte() {
    unsigned char i, dat = 0;
    for(i = 0; i < 8; i++) {
        dat <<= 1;
        
        // 1. 产生时钟脉冲 (先拉高时钟让从机输出数据)
        RC522_SCK = 0;      // 物理高
        _nop_();
        
        // 2. 读取数据 (MISO 直连，直接读)
        if(RC522_MISO) 
            dat |= 0x01;
            
        // 3. 恢复时钟空闲
        RC522_SCK = 1;      // 物理低
    }
    return dat;
}

// ==========================================
// 4. RC522 寄存器读写 (协议层)
// ==========================================

// RC522 写寄存器
// Address: 寄存器地址 (0x00 - 0x3F)
// Value:   写入的数据
void RC522_WriteReg(unsigned char addr, unsigned char val) {
    // 地址格式：[6 位地址][1 位 0(写)][1 位 0] -> 实际发送 (addr << 1) & 0x7E
    RC522_NSS = 0;                  // 选中芯片 (P1.1 直连，0 有效)
    RC522_SPI_WriteByte((addr << 1) & 0x7E); 
    RC522_SPI_WriteByte(val);
    RC522_NSS = 1;                  // 取消选中
}

// RC522 读寄存器
// Address: 寄存器地址
// 返回值：读取的数据
unsigned char RC522_ReadReg(unsigned char addr) {
    unsigned char val;
    // 地址格式：[6 位地址][1 位 1(读)][1 位 0] -> 实际发送 ((addr << 1) & 0x7E) | 0x80
    RC522_NSS = 0;
    RC522_SPI_WriteByte(((addr << 1) & 0x7E) | 0x80);
    val = RC522_SPI_ReadByte();
    RC522_NSS = 1;
    return val;
}

// ==========================================
// 5. 初始化与复位 (匹配硬件反向逻辑)
// ==========================================
void RC522_Init() {
    // 1. 配置 P4 口模式 (推挽输出，至关重要)
    // STC15 默认 P4 可能是准双向，驱动 SPI 需推挽
    P4M0 = 0x1E;  // 0001 1110 (P4.1-P4.4 推挽)
    P4M1 = 0x00;
    
    // 2. 配置 P1 口 (MISO 输入，NSS 输出)
    P1M0 &= ~0x03; 
    P1M1 |= 0x01;  // P1.0 高阻输入
    P1M1 &= ~0x02; // P1.1 推挽/准双向
    
    // 3. 设置 SPI 模式 (P4.4)
    // RC522 要求 SPI 模式下该引脚通常为低电平 (物理)
    // 因有反向器，MCU 需输出 1
    RC522_MODE = 1; 
    
    // 4. 硬件复位 (P4.3)
    // RC522 Reset 低电平有效 (物理)
    // 因有反向器，MCU 输出 1 = 物理 0 (复位)
    RC522_RST = 1;      // 开始复位
    Delay_us(100);      
    RC522_RST = 0;      // 结束复位 (物理高)
    Delay_us(100);
    
    // 5. 软复位 (通过 CommandReg)
    RC522_WriteReg(0x01, 0x0F); // CommandReg, SoftReset
    
    // 6. 设置定时器 (例如 13ms 周期)
    RC522_WriteReg(0x2A, 0x8D); // TModeReg
    RC522_WriteReg(0x2B, 0x8E); // TPrescalerReg
    RC522_WriteReg(0x2C, 0x3E); // TReloadValH
    RC522_WriteReg(0x2D, 0x31); // TReloadValL
    
    // 7. 设置 TX 配置
    RC522_WriteReg(0x15, 0x40); // TxASKReg
    RC522_WriteReg(0x11, 0x00); // ModeReg (UART 关闭，SPI 启用)
}