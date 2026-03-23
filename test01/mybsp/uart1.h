#ifndef __UART1_H__
#define __UART1_h__
#include <sys.h>

/*
支持的波特率：
1200, 2400, 4800, 9600, 19200, 38400, 57600
其他值会被设置为9600
建议使用9600及以下
*/

extern void uart1Init(unsigned long baudrate);
extern void uart1Send(unsigned char* content, unsigned char num); // 发送的数据，指针和大小
extern void setUart1Buf(unsigned char* buf, unsigned char buf_num, unsigned char* head, unsigned char head_num); // 设置接收到数据后保存的位置和包头

#endif