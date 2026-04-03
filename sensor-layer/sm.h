#ifndef __SM_H__
#define __SM_H__
#include <sys.h>


extern void smInit();
extern void setSm(unsigned char sm, unsigned char speed, unsigned int steps, unsigned char dir);

// 设置速度(平滑过度，也可以直接调用setSm设置，此时会直接将速度改为设置的速度)
extern void setSpeed(unsigned char sm, unsigned char speed); 
extern void setAcc(unsigned char sm, char acc); // 设置加速度
/*
sm指定步进电机
	0 -- SM模块外接的电机
	1 -- L0-L3模拟的步进电机
	2 -- L4-L5模拟的步进电机
speed控制旋转速度
	每步的时间：1000/speed
	范围 1-255  -- 速度不要设置为0，此外255用于setSpeed中初始化目标速度，如果要设置255只能调用setSm
	speed不要设置0，如果需要电机停止，设置steps为0
	此外由于实现原因，在speed很小（1或2时），led无法正常显示，推荐speed在2以上
steps指定旋转的步数，控制循环
dir指定方向
	0 -- 正转
	1 -- 反转
*/

#endif