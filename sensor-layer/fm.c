#include "regdef.h"

// 定义 IAP15F2K61S2 的特殊功能寄存器
sbit SCL = P4^5; // SCLK -> P4.5
sbit SDA = P2^7; // SDIO -> P2.7
sfr WDT_CONTR = 0xC1;

xdata unsigned int _fre = 1061;
xdata unsigned char _fm_volume = 15; // 0-15

unsigned char fm_init_data[8] = {
		0xD0, 0x11,   // reg02
		0x24, 0x58,   // reg03
		0x00, 0x2A,   // reg04
		0x00, 0x8F    // reg05
};

// 延时函数（适用于 12MHz 晶振）
void delay_us(unsigned int us){
    xdata unsigned char i;
    while (us--) {
        i = 3; while (i--);
    }
}

void delay_ms(unsigned int ms){
    xdata unsigned char i, j;
    for (i = ms; i > 0; i--)
        for (j = 123; j > 0; j--);
}

void fmInit(){
	P2M1 |= 0x80; P2M0 |= 0x80;
	P4M1 |= 0x20; P4M0 |= 0x20;
}

// I2C 启动条件
void I2C_Start(void){
    SDA = 1;
    SCL = 1;
    delay_us(5);
    SDA = 0;
    delay_us(5);
    SCL = 0;
}

// I2C 停止条件
void I2C_Stop(void){
    SDA = 0;
    SCL = 1;
    delay_us(5);
    SDA = 1;
}

// 发送一个字节，返回 ACK (0=ACK, 1=NACK)
bit I2C_WriteByte(unsigned char dat){
    xdata unsigned char i;
    bit ack;
    for(i = 0; i < 8; i++){
        if (dat & 0x80) SDA = 1; else SDA = 0;
        dat <<= 1;
        delay_us(5);
        SCL = 1;
        delay_us(5);
        SCL = 0;
    }
    SDA = 1;  // 释放 SDA
    delay_us(5);
    SCL = 1;
    delay_us(5);
    ack = SDA;  // 读 ACK
    SCL = 0;
    return ack;
}

// RDA5807FP 专用写入：从固定 reg 0x02 开始连续写入 len 字节数据
void RDA5807_WriteBytes(unsigned char *dat, unsigned char len){
    xdata unsigned char i;
    I2C_Start();
    if (I2C_WriteByte(0x20)) {  // 写地址 0x20 (7位地址 0x10)
        I2C_Stop();
        return;
    }
    for (i = 0; i < len; i++) {
        if (I2C_WriteByte(dat[i])) break;
    }
    I2C_Stop();
}

// 初始化 RDA5807FP (固定 87.5 MHz, 最大音量, 12MHz 时钟, 点亮三个LED)
void RDA5807_Init(void){
    // 软复位：reg 0x02 low=0x02 (SOFT_RESET=1), high=0x00
    xdata unsigned char reset_data[2] = {0x00, 0x02};
    RDA5807_WriteBytes(reset_data, 2);
    delay_ms(10);

    // 清除复位：reg 0x02 low=0x00, high=0x00
    reset_data[1] = 0x00;
    RDA5807_WriteBytes(reset_data, 2);
    delay_ms(10);
    

    RDA5807_WriteBytes(fm_init_data, 8);
    delay_ms(50);  // 调谐完成延时
}

void update_params(unsigned int fre, unsigned char vol){
	xdata unsigned int tmp;
	tmp = ((fre-760)<<6)+0x18;
	fm_init_data[2] = (tmp>>8);
	fm_init_data[3] = (unsigned char)(tmp&0x00ff);
	fm_init_data[7] = ((0x80) + vol);
	RDA5807_Init();
}

void stopFM(){
	xdata unsigned char reset_data[2] = {0x00, 0x02};
	RDA5807_WriteBytes(reset_data, 2);
	delay_ms(10);
}