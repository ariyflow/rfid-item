#include "DS1302.h"
#include "regdef.h"

sfr P5 = 0xC8;
sfr P5M1 = 0xC9;
sfr P5M0 = 0xCA;
sbit SCLK = P1^5; // 串行时钟引脚
sbit SDA = P5^4; // 数据输入/输出引脚
sbit RST = P1^6; // 复位引脚

#define _bcd_to_dec(num) (((num>>4)*10)+(num&0x0f))
#define _dec_to_bcd(num) ((((num)/10)<<4)+(num%10))

unsigned char readDS1302(unsigned char address){
	xdata unsigned char i, temp = 0x00;
	address = (address<<1)+0x81;
	
	P5M1 &= ~(1<<4);
	P5M0 |=  (1<<4);
	
	RST = 0; _nop_();
	SCLK = 0; _nop_();
	RST = 1; _nop_();

	// 写入地址
	for(i = 0; i < 8; i++){
		SDA = address & 0x01;
		address >>= 1;
		SCLK = 1;
		_nop_();
		SCLK = 0;
	}
	
	P5M1 |=  (1<<4);
	P5M0 &= ~(1<<4);

	// 切换为读取模式
	for(i = 0; i < 8; i++){
		temp >>= 1;
		if(SDA) temp |= 0x80;
		SCLK = 1;
		_nop_();
		SCLK = 0;
	}

	RST = 0; _nop_();
	return temp;
}

void writeDS1302(unsigned char address, unsigned char dat){
	xdata unsigned char i;
	address = (address<<1)+0x80;
	
	P5M1 &= ~(1<<4);
	P5M0 |=  (1<<4);
	
	RST = 0; _nop_();
	SCLK = 0; _nop_();
	RST = 1; _nop_();

	// 发送地址（8位，LSB first）
	for(i = 0; i < 8; i++){
			SDA = address & 0x01;
			address >>= 1;
			SCLK = 1;
			_nop_();
			SCLK = 0;
			_nop_();
	}

	// 发送数据（8位，LSB first）
	for(i = 0; i < 8; i++){
			SDA = dat & 0x01;
			dat >>= 1;
			SCLK = 1;
			_nop_();
			SCLK = 0;
			_nop_();
	}

	RST = 0; _nop_();
}

Date getDate(){
	xdata Date tmp;
	tmp.second = readDS1302(0);
	tmp.minute = readDS1302(1);
	tmp.hour = readDS1302(2);
	tmp.day = readDS1302(3);
	tmp.month = readDS1302(4);
	tmp.year = readDS1302(6);
	
	tmp.second = (tmp.second>>4)*10+(tmp.second&0x0f);
	tmp.minute = (tmp.minute>>4)*10+(tmp.minute&0x0f);
	tmp.hour = (tmp.hour>>4)*10+(tmp.hour&0x0f);
	tmp.day = (tmp.day>>4)*10+(tmp.day&0x0f);
	tmp.month = (tmp.month>>4)*10+(tmp.month&0x0f);
	tmp.year = (tmp.year>>4)*10+(tmp.year&0x0f);
	return tmp;
}
void writeDate(Date d){
	writeDS1302(7,0x00);
	writeDS1302(0,_dec_to_bcd(d.second));
	writeDS1302(1,_dec_to_bcd(d.minute));
	writeDS1302(2,_dec_to_bcd(d.hour));
	writeDS1302(3,_dec_to_bcd(d.day));
	writeDS1302(4,_dec_to_bcd(d.month));
	writeDS1302(6,_dec_to_bcd(d.year));
	writeDS1302(7,0x80);
}

void wRAM(unsigned char address, unsigned char dat){ // 读写RAM
	xdata unsigned char i;
	writeDS1302(7,0x00);
	address = (address<<1)+0xC0;
	
	P5M1 &= ~(1<<4);
	P5M0 |=  (1<<4);
	
	RST = 0; _nop_();
	SCLK = 0; _nop_();
	RST = 1; _nop_();

	// 发送地址（8位，LSB first）
	for(i = 0; i < 8; i++){
			SDA = address & 0x01;
			address >>= 1;
			SCLK = 1;
			_nop_();
			SCLK = 0;
			_nop_();
	}

	// 发送数据（8位，LSB first）
	for(i = 0; i < 8; i++){
		SDA = dat & 0x01;
		dat >>= 1;
		SCLK = 1; // 上升沿传数据
		_nop_();
		SCLK = 0;
		_nop_();
	}

	RST = 0; _nop_();
	writeDS1302(7,0x80);
}

unsigned char rRAM(unsigned char address){
	xdata unsigned char i, temp = 0x00;
	address = (address<<1)+0xC1;
	
	P5M1 &= ~(1<<4);
	P5M0 |=  (1<<4);
	
	RST = 0; _nop_();
	SCLK = 0; _nop_();
	RST = 1; _nop_();

	// 写入地址
	for(i = 0; i < 8; i++){
		SDA = address & 0x01;
		address >>= 1;
		SCLK = 1;
		_nop_();
		SCLK = 0;
	}
	
	P5M1 |=  (1<<4);
	P5M0 &= ~(1<<4);

	// 切换为读取模式
	for(i = 0; i < 8; i++){
		temp >>= 1;
		if(SDA) temp |= 0x80;
		SCLK = 1;
		_nop_();
		SCLK = 0;
	}

	RST = 0; _nop_();
	return temp;
}