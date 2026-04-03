#include "AT24C02.h"
#include "regdef.h"

sfr P5 = 0xC8;
sfr P5M1 = 0xC9;
sfr P5M0 = 0xCA;

sbit IIC_SDA = P4^0;
sbit IIC_SCL = P5^5;

static void delay_us(unsigned int us){
    xdata unsigned char i;
    while (us--) {
        i = 3; while (i--);
    }
}

static void delay_ms(unsigned int ms){
    xdata unsigned char i, j;
    for (i = ms; i > 0; i--)
        for (j = 123; j > 0; j--);
}


void ATInit(){
	// IIC 使用开漏
	P5M1 |= (1<<5); P5M0 |= (1<<5);
	P4M1 |= (1<<0); P4M0 |= (1<<0);
}

void _AT_IIC_Start(void){
	IIC_SCL = 1;
	IIC_SDA = 1;
	delay_us(5);
	IIC_SDA = 0;
	delay_us(5);
	IIC_SCL = 0;
}

void _AT_IIC_Stop(void){
	IIC_SDA = 0;
	IIC_SCL = 1;
	delay_us(5);
	IIC_SDA = 1;
}

// 该函数为直写入IIC_SDA
bit _AT_WriteByte(unsigned char dat){
	xdata unsigned char i;
	bit ack;
	
	// 直接写入dat到IIC_SDA
	for(i=0;i<8;i++){
		if(dat & 0x80) IIC_SDA = 1;
		else IIC_SDA = 0;
		dat<<=1;
		delay_us(5);
		IIC_SCL = 1;
		delay_us(5);
		IIC_SCL = 0;
	}
	
	IIC_SDA = 1;
	delay_us(5);
	IIC_SCL = 1;
	delay_us(5);
	ack = IIC_SDA;
	IIC_SCL = 0;
	return ack;
}

// 从 I2C 总线读取一个字节
unsigned char _AT_ReadByte(bit ack){
	xdata unsigned char i;
	xdata unsigned char dat = 0;
	IIC_SDA = 1;  // 释放总线（准备读）

	for(i = 0; i < 8; i++){
		IIC_SCL = 1;
		delay_us(5);
		dat <<= 1;
		if(IIC_SDA) dat |= 0x01;   // 读取 SDA 电平
		IIC_SCL = 0;
		delay_us(5);
	}

	// 主机发送 ACK/NACK
	if(ack){
		IIC_SDA = 1;  // NACK
	}
	else{
		IIC_SDA = 0;  // ACK
	}
	delay_us(5);
	IIC_SCL = 1;
	delay_us(5);
	IIC_SCL = 0;
	IIC_SDA = 1;  // 释放 SDA（为 Stop 做准备）

	return dat;
}

unsigned char rAT(unsigned char addr){
	xdata unsigned char dat;
	xdata unsigned char device_addr = 0xA0;  // AT24C02 写地址

	// Step 1: Start
	_AT_IIC_Start();

	// Step 2: Send device write address (0xA0)
	if(_AT_WriteByte(device_addr)){
			_AT_IIC_Stop();
			return 0xFF;  // 地址无应答，返回错误值
	}

	// Step 3: Send memory address to read from
	if(_AT_WriteByte(addr)){
			_AT_IIC_Stop();
			return 0xFF;  // 地址写入无应答
	}

	// Step 4: Repeated Start
	_AT_IIC_Start();

	// Step 5: Send device read address (0xA1)
	if(_AT_WriteByte(device_addr | 0x01)){
			_AT_IIC_Stop();
			return 0xFF;  // 读地址无应答
	}

	// Step 6: Read one byte, send NACK
	dat = _AT_ReadByte(1);  // 1 = NACK

	// Step 7: Stop
	_AT_IIC_Stop();

	return dat;
}

void wAT(unsigned char addr, unsigned char val){
    xdata unsigned char device_addr = 0xA0;  // AT24C02 的 I2C 写地址（7位地址 0x50 << 1 | 0）

    // Step 1: Start
    _AT_IIC_Start();

    // Step 2: Send device write address (0xA0)
    _AT_WriteByte(device_addr);   // 可加应答检查，但此处简化

    // Step 3: Send memory address
    _AT_WriteByte(addr);

    // Step 4: Send data byte
    _AT_WriteByte(val);

    // Step 5: Stop — 触发 EEPROM 内部写入
    _AT_IIC_Stop();

    // Step 6: 等待写周期完成（典型值 5ms，最大 10ms）
    delay_ms(50);  // 必须延时！否则下一次操作可能失败
}