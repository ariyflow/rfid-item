#include <sys.h>
#include "ir.h"


xdata userCallback userCallbacks[10] = {NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL}; // 用户绑定的函数地址
xdata unsigned int eventID = 0x0000;
xdata unsigned char time_flag = 0;
xdata unsigned char _i;
xdata int _speed_delta = 0;

extern xdata unsigned char keyPress;
extern xdata unsigned char _adckeyPress;
extern void disRun();
extern void _smRun(unsigned char sm);
extern xdata unsigned char _speeds[3];
extern xdata char _acc[3];
extern xdata unsigned char _target_speed[3];

// ct为0时用作定时器，ct为1时用作计数器，输入0即可
void t0Init(unsigned char ct){
	TMOD = (TMOD&0xf0) + (ct << 2) + 0x10; // 设置mode,GATE=0, C/T由用户决定, 模式选择为8位自动重装载
	AUXR = (AUXR&0x7f) + 0x80; // 设置不分频，速度乘12，保证中断次数
	TR0 = 1;
	ET0 = 1;
	EA = 1;
}

// 使用该函数替代原先的初始化
void Timer0Init(void)		//1毫秒@11.0592MHz
{
	AUXR |= 0x80;		//定时器时钟1T模式
	TMOD &= 0xF0;		//设置定时器模式
	TL0 = 0xCD;		//设置定时初值
	TH0 = 0xD4;		//设置定时初值
	TF0 = 0;		//清除TF0标志
	TR0 = 1;		//定时器0开始计时
	
	// 开启中断
	ET0 = 1;
	EA = 1;
}

void interruptInit(){
	EA = 1; // 总中断开关
	EX0 = 1; // 中断0，控制key1
	EX1 = 1; // 中断1，控制key2
	IT0 = 1; // 只在下降沿触发，即key1按1次触发1次中断
	IT1 = 1; // 只在下降沿触发，即key2按1次触发1次中断
}

void sysInit(){
	interruptInit();
	Timer0Init();
}

void setCallback(char id, userCallback user_callback){
	userCallbacks[id] = user_callback;
}



void eventParse(){
	if((eventID & 0x01) == 0x01){ // 事件0 -- key1或key2按下
		if(userCallbacks[0])userCallbacks[0]();
		keyPress = 0;
		eventID = (eventID^0x01);
	}
	else if((eventID & 0x10) == 0x10){ // 事件4 -- 串口1收到数据包
		
		if(userCallbacks[4])userCallbacks[4]();
		eventID = (eventID^0x10);
	}
	else if((eventID & 0x20) == 0x20){ // 事件5 -- adc按键
		if(userCallbacks[5])userCallbacks[5]();
		_adckeyPress = 0;
		eventID = (eventID^0x20);
	}
	else if((eventID & 0x80) == 0x80){ // 事件7 -- 串口2收到信息

		if(userCallbacks[7])userCallbacks[7]();

		eventID = (eventID^0x80);
	}
}

void sysRun(){
	static unsigned int _cnt = 0;
	static char xdata key1down = 0;
	static char xdata key2down = 0;
	eventParse();
	
	if(time_flag == 1){

		// 这里是每次中断都需要执行的操作
		// 重新装载初始化的值
		TL0 = 0xCD;
		TH0 = 0xD4;
		
		if(userCallbacks[1])userCallbacks[1](); // 触发int1事件
		
		
		// 监测是否需要更新步进电机
//		for(_i=0;_i<3;_i++){
//			if(_cnt%(1000/_speeds[_i]) == 0){
//				_smRun(_i);
//			}
//		}
		
		if(KEY1 == 0){ // key1的触发事件
			
			if(key1down == 10){ // 确认为有效事件
				// if(userCallbacks[0])userCallbacks[0]();// 调用第一个回调函数
				eventID = (eventID^(1<<enumEventKey));
				keyPress ^= 0x01; // 标志发生按下事件的位置
				
				++key1down;
			}
			else if(key1down < 10){
				++key1down;
			}
		}
		else key1down = 0;
		
		if(KEY2 == 0){ // key2的触发事件
			
			if(key2down == 10){ // 确认为有效事件
				// if(userCallbacks[1])userCallbacks[1]();// 调用第一个回调函数
				eventID = (eventID^(1<<enumEventKey));
				keyPress ^= 0x02;
				++key2down;
			}
			else if(key2down < 10){
				++key2down;
			}
		}
		else key2down = 0;
		
		// 每10次中断执行的操作
		if(_cnt%10 == 0){
			if(userCallbacks[2])userCallbacks[2]();
		}
		
		// 每100次中断执行的操作
		if(_cnt%100 == 0){
			if(userCallbacks[3])userCallbacks[3]();
		}
		
		if(_cnt%1000 == 0){
			
			if(userCallbacks[6])userCallbacks[6]();
			
			// 运行1s后，清空计数，如果设置了加速度的话给电机加速
//			for(_i=0;_i<3;_i++){
//				if(_target_speed[_i] != 0xff){ // 平滑过度到目标速度
//					_speed_delta = _target_speed[_i] - _speeds[_i];
//					
//					if(_speed_delta > 0){ // 加速
//						if(_speed_delta > 55 && _acc[_i] < 10){
//							_acc[_i]++;
//						}
//						else{
//							if(_acc[_i] > 3 && _speed_delta > 10)_acc[_i]--;
//							else if(_speed_delta > 2)_acc[_i] = 2;
//							else _acc[_i] = 1;
//						}
//					}
//					else if(_speed_delta < 0){ // 减速
//						if(_speed_delta < -55 && _acc[_i] > -10)_acc[_i]--;
//						else{
//							if(_acc[_i] < -3 && _speed_delta < -10)_acc[_i]++;
//							else if(_speed_delta < -2)_acc[_i] = -2;
//							else _acc[_i] = -1;
//						}
//					}
//					else {// 达到预设速度
//						_target_speed[_i] = 0xff;
//						_acc[_i] = 0;
//					}
//				}

//				_speeds[_i] += _acc[_i];
//			}
			_cnt = 0;
		}
		_cnt++;
		time_flag = 0;
	}
}

// 下面是中断的处理逻辑，该中断每1ms执行一次



extern unsigned char buf[6];
extern void uart1Send(unsigned char* content, unsigned char num);

void Timer0_Routine(void) interrupt 1{
	time_flag = 1;
	disRun();
}

// 中断0，由key1键按下引起的中断
void Int0_Routine(void) interrupt 0{
	// if(userCallbacks[0])userCallbacks[0](); // 调用第一个回调函数
}


// 由key2键按下引起的中断
void Int1_Routine(void) interrupt 2{
	// if(userCallbacks[1])userCallbacks[1]();
}