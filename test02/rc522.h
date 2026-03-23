#ifndef __RC522_H__
#define __RC522_H__

#include <STC15F2K60S2.H>

// ==========================================
// 引脚定义 (严格匹配指导书与硬件反向器)
// ==========================================
sbit MF522_SO   = P1^0;   // MISO (直连，输入)
sbit MF522_NSS  = P1^1;   // NSS  (直连，输出，低有效)
sbit MF522_SCK  = P4^1;   // SCK  (反向器，输出)
sbit MF522_SI   = P4^2;   // MOSI (反向器，输出)
sbit MF522_EA   = P4^3;   // RST  (反向器，输出)
sbit MF522_IIC  = P4^4;   // MODE (反向器，输出)

// ==========================================
// 寄存器地址定义
// ==========================================
#define CommandReg        0x01
#define VersionReg        0x37

// ==========================================
// 函数声明
// ==========================================
void RC522Init(void);
unsigned char ReadRawRC(unsigned char Address);
void WriteRawRC(unsigned char Address, unsigned char value);
unsigned char CheckVersion(void);

#endif