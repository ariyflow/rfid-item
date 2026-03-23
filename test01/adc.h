#ifndef __ADC_H__
#define __ADC_H__
#include <sys.h>

/*
adc各个位的数模转换映射：
.1.0 -- 扩展接口
.2 -- 霍尔
.3 -- 温度
.4 -- 光照
.7 -- 导航键+key3
*/

typedef struct{
	unsigned int adcP0;
	unsigned int adcP1;
	unsigned int adcHall;
	unsigned int adcTem;
	unsigned int adcLum; // 注意光照使用int
	unsigned int adcNav;
} ADC;

extern void adcInit();
extern ADC getAdc();
extern unsigned char getADCKeyAct(unsigned char key);

enum adcKey{
	enumADCKey3,
	enumADCKeyRight,
	enumADCKeyDown,
	enumADCKeyCenter,
	enumADCKeyLeft,
	enumADCKeyUp
};

#endif