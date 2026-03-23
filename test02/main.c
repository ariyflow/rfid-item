#include <STC15F2K60S2.H>
#include "rc522.h"
#include <intrins.h>
#include "uart1.h"

xdata unsigned int eventID = 0x00;
xdata unsigned char rcv_buf[24]; // 接收数据的缓冲区
code unsigned char head[2] = {0xaa, 0x55}; // 数据包头

void delay_ms(unsigned int xms)		//@11.0592MHz
{
	unsigned char i, j;
	
	while(xms--){
		_nop_();
		_nop_();
		_nop_();
		i = 11;
		j = 190;
		do
		{
			while (--j);
		} while (--i);
	}
}

void uart1Callback(){
	uart1Send(rcv_buf, 24);
}

void sysRun(){
	if((eventID & 0x01)){ // 串口收到数据
		uart1Callback();
	}
}

void main() {
	unsigned char ver;
	uart1Init(9600);
	RC522Init();
	delay_ms(1000);
	
	// setUart1Buf(rcv_buf, 24, head, 2);
   
	while(1) {
		ver = CheckVersion();
		uart1Send(&ver, 1);
		sysRun();
	}
}