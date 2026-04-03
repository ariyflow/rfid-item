#include "uart2.h"
#include "regdef.h"
#include "sys.h"
#include "display.h"

sfr P3M1 = 0xB1;
sfr P3M0 = 0xB2;
sfr IE2 = 0xAF;
sfr IP2 = 0xB5;
sfr S2CON = 0x9A;
sfr P_SW2 = 0xBA;
sbit ENABLE_485 = P3^7;
sfr S2BUF = 0x9B;

sfr T2H = 0xD6;
sfr T2L = 0xD7;

extern xdata unsigned int eventID;

xdata unsigned char _buf2_cursor = 0;
xdata unsigned char _buf2_num = 2;
xdata unsigned char* _buf2;

void uart2Init(unsigned long baudrate){
	unsigned int reload;
	// 配置 P3.7 (DE/RE), P4.7 (TX), P4.6 (RX)
	P3M1 &= ~0x80;  P3M0 |=  0x80;   // P3.7: Push-Pull
	P4M1 &= ~0x80;  P4M0 |=  0x80;   // P4.7: Push-Pull
	P4M1 |=  0x40;  P4M0 &= ~0x40;   // P4.6: High-Z Input

	// 配置 Timer2 为 1T 模式，作为 UART2 波特率发生器
	reload = 65536 - (11059200 / baudrate);
	AUXR &= ~0x18;          // 清除 T2R (bit4) 和 T2_CT (bit3)
	AUXR |=  0x04;          // 设置 T2x12=1 (1T mode)
	if(baudrate == 1200){
		T2L = 0x00; T2H = 0xf7;
	}
	else if(baudrate == 2400){
			T2L = 0x50; T2H = 0xfb;
	}
	else if(baudrate == 4800){
			T2L = 0xc0; T2H = 0xfd;
	}
	else if(baudrate == 9600){
			T2L = 0xe0; T2H = 0xfe;
	}
	else if(baudrate == 19200){
			T2L = 0x70; T2H = 0xff;
	}
	else if(baudrate == 38400){
			T2L = 0xb8; T2H = 0xff;
	}
	else if(baudrate == 57600){
			T2L = 0xd0; T2H = 0xff;
	}
	else if(baudrate == 115200){
			T2L = 0xe8; T2H = 0xff;
	}

	AUXR |= 0x10;           // 启动 Timer2 (T2R=1)

	// 初始化 UART2
	S2CON = 0x10;           // 8-bit UART, REN=1, TI/RI=0
	P_SW2 = (P_SW2 & ~0x01) | 0x01; // 切换 UART2 到 P4.6/P4.7
	ENABLE_485 = 0;  // 默认接收状态
	IP2  |= 0x01;           // UART2 高优先级
	IE2  |= 0x01;           // 使能 UART2 中断
}

void uart2Send(unsigned char* content, unsigned char num){
	unsigned char* tmp;
	IE2 &= ~0x01;
	
	tmp = content;
	ENABLE_485 = 1;
	
	while(num--){
		S2BUF = *tmp;
		while((S2CON&0x02) == 0);
		S2CON &= ~(1<<1);
		tmp++;
	}

	ENABLE_485 = 0;
	IE2 |= 0x01;
}

void setUart2Buf(unsigned char* buf, unsigned char buf_num){
	_buf2 = buf;
	_buf2_num = buf_num;
}

void UART2_Routine(void) interrupt 8{

	if(S2CON&0x02)S2CON &= ~(1<<1);
	
	if(S2CON&0x01){
		
		if(_buf2_cursor < _buf2_num){
			_buf2[_buf2_cursor] = S2BUF;
			_buf2_cursor = _buf2_cursor+1;
			
			
			if(_buf2_cursor>=_buf2_num){ // 缓冲区满，进行判断
				
				_buf2_cursor = 0;
				eventID = (eventID|(1<<enumEventUart2)); // 触发事件
			}
		}
		
		
		S2CON &= ~(1<<0);
	}
}