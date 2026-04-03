#include <sm.h>

extern void udelay(unsigned int us);
extern xdata unsigned char _dis_shape;
xdata unsigned char _speeds[3] = {0,0,0};
xdata unsigned int _steps[3] = {0,0,0};
xdata unsigned char _dirs[3] = {0,0,0};
xdata char _acc[3] = {0x00,0x00,0x00};

/*
code unsigned char sm_table[8][4] = {
	{0,1,1,1},
	{0,0,1,1},
	{1,0,1,1},
	{1,0,0,1},
	{1,1,0,1},
	{1,1,0,0},
	{1,1,1,0},
	{0,1,1,0}
};
*/

code unsigned char sm_table[8][4] = {
	{1,0,0,0},
	{1,1,0,0},
	{0,1,0,0},
	{0,1,1,0},
	{0,0,1,0},
	{0,0,1,1},
	{0,0,0,1},
	{1,0,0,1}
};

void smInit(){
	P4M1 = 0x00; // 设置推挽
	P4M0 = 0x1E;
}

void _setSM(unsigned char s){ // s是sm_table的索引 0-7
	S1 = sm_table[s][0];
	S2 = sm_table[s][1];
	S3 = sm_table[s][2];
	S4 = sm_table[s][3];
}

// 由于setLed只能整体赋值，无法对某几个分别赋值，这里直接操作displayer中的dis_shape
// 还需要直接设置P0的值显示，否则只有在进入while循环的disRun才会更新显示
void _setSM1(unsigned char s){ // 这里s也是索引
	_dis_shape = (_dis_shape&0xf0)|sm_table[s][0]|(sm_table[s][1]<<1)|(sm_table[s][2]<<2)|(sm_table[s][3]<<3);
}

void _setSM2(unsigned char s){
	_dis_shape = (_dis_shape&0x0f)|((sm_table[s][0]|(sm_table[s][1]<<1)|(sm_table[s][2]<<2)|(sm_table[s][3]<<3))<<4);
}

void setSm(unsigned char sm, unsigned char speed, unsigned int steps, unsigned char dir){
	_speeds[sm] = speed;
	_steps[sm] = steps;
	_dirs[sm] = dir;
	/*
	unsigned int i;
	if(sm == 0){ // SM外接的步进电机
		if(dir == 0){ // 正转
			for(i=0;i<steps;i++){
				_setSM(i%8);
				Delay(1000/speed);
			}
		}
		else{
			
			for(i=0;i<steps;i++){
				_setSM(7-(i%8));
				Delay(1000/speed);
			}
			
		}
	}
	else if(sm == 1){ // L0-L3 模拟的步进电机
		if(dir == 0){ // 正转
			for(i=0;i<steps;i++){
				_setSM1(i%8);
				Delay(1000/speed);
			}
		}
		else{
			
			for(i=0;i<steps;i++){
				_setSM1(7-(i%8));
				Delay(1000/speed);
			}
			
		}
	}
	else if(sm == 2){ // L4-L7 模拟的步进电机
		if(dir == 0){ // 正转
			for(i=0;i<steps;i++){
				_setSM2(i%8);
				Delay(1000/speed);
			}
		}
		else{
			
			for(i=0;i<steps;i++){
				_setSM2(7-(i%8));
				Delay(1000/speed);
			}
			
		}
	}
	else return;
	*/
}

// 该函数在定时器中断中调用，用于执行一次步进电机的转动
void _smRun(unsigned char sm){ // sm为需要执行的电机
		// 控制步进电机的转动 暂时没有速度
	if(sm == 0){
		if(_steps[0]){
			if(_dirs[0])_setSM(7-(_steps[0]%8));
			else _setSM(_steps[0]%8);
			--_steps[0];
		}
	}
	else if(sm == 1){
		
		if(_steps[1]){
			if(_dirs[1])_setSM1(7-(_steps[1]%8));
			else _setSM1(_steps[1]%8);
			--_steps[1];
		}
	}
	else if(sm == 2){
		
		if(_steps[2]){
			if(_dirs[2])_setSM2(7-(_steps[2]%8));
			else _setSM2(_steps[2]%8);
			--_steps[2];
		}
	}
}

void setAcc(unsigned char sm, char acc){
	_acc[sm] = acc;
}

xdata unsigned char _target_speed[3] = {0xff,0xff,0xff};
void setSpeed(unsigned char sm, unsigned char speed){
	_target_speed[sm] = speed;
}