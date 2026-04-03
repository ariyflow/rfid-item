#ifndef __AT24C02_H__
#define __AT24C02_h__

/*
0,1 - 保存点赞数 0保存高8bit 1保存低8bit
*/

extern void ATInit();
extern unsigned char rAT(unsigned char addr);
extern void wAT(unsigned char addr, unsigned char val);

#endif