#ifndef __DISPLAY_H__
#define __DISPLAY_H__

extern void disInit(); // 初始化
extern void setLed(char led_vector); // led显示
extern void setSeg(char s0, char s1,char s2, char s3,char s4, char s5,char s6, char s7); // 数码管显示
extern void disRun(); // 每次调用显示某一个数码管或者led，休眠100us，也就是说调用9次可以显示所有数码管和led，休眠900us
extern void setNum(unsigned long num);
extern void addPoint(unsigned char cur);
#endif