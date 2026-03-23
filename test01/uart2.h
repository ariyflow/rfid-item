#ifndef __UART2_H__
#define __UART2_H__

/*
	uart2设计逻辑与uart1基本相同，使用定时器二产生波特率
*/
extern void uart2Init(unsigned long baudrate);
extern void uart2Send(unsigned char* content, unsigned char num);
extern void setUart2Buf(unsigned char* buf, unsigned char buf_num);

#endif