#ifndef __SYS_H__
#define __SYS_H__

#ifndef NULL
#define NULL ((void*)0)
#endif

#include <regdef.h>

/*
核心控制，原本独立的timer.h用于控制定时器0，现在嵌入到sys中
*/

typedef void (*userCallback)(void);

extern void sysInit();
extern void setCallback(char id, userCallback user_callback); // 绑定用户的回调函数
extern void sysRun();

enum event{
	enumEventKey, // 按键按下（key1或key2）
	enumEventInt1, // 定时器0中断1次 -- 这三个中断相关的事件会直接在T0中断里调用
	enumEventInt10, // 定时器0中断10次
	enumEventInt100, // 定时器0中断100次
	enumEventUart1, // 串口1收到合法数据包
	enumEventAdcKey, // adc上的按键按下
	enumEventInt1000, // 中断1000次，1s后
	enumEventUart2 // 串口2收到数据包
};

extern void eventParse(); // 处理事件的函数，在while循环中调用

#endif