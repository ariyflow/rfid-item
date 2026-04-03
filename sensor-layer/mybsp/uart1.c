#include <uart1.h>

extern xdata unsigned int eventID;

xdata unsigned char* _buf;
xdata unsigned char* _head;
xdata unsigned char _buf_num = 0, _head_num = 0;
xdata unsigned char _buf_cursor = 0; // 当前buf的游标
xdata unsigned char _init_suf = 0; // 填充定时器初值的值
// 接收到一个字节的数据后，触发中断，在中断函数中获取数据并进行判断

code unsigned long _baudrate_table[7][2] = {
	{1200, 0xE8},
	{2400, 0xF4},
	{4800, 0xFA},
	{9600, 0xFD},
	{19200, 0xFE},
	{38400, 0xFF},
	{57600, 0xFF}
};

unsigned char _get_initial_value(unsigned long baudrate){
	xdata unsigned char _ui;
	for(_ui=0;_ui<7;_ui++){
		if(_baudrate_table[_ui][0] == baudrate)return _baudrate_table[_ui][1];
	}
	return 0xFD;
}

void uart1Init(unsigned long baudrate){
	SCON = 0x50; // .7.6设置模式，此处使用模式1，即使用定时器1，REN置1，SM2置0
	TMOD = (TMOD&0x0f)+(0x20); // 定时器1设置为模式2（8位自动重装载）
	
	_init_suf = _get_initial_value(baudrate);
	TH1 = _init_suf;
	TL1 = _init_suf;
	
	TR1 = 1; // 启动定时器1
	AUXR = (AUXR&0xfe); // 辅助寄存器最后一位置0，表示串口1使用定时器1
	
	// 开启中断
	ES = 1;
	EA = 1;
}


void uart1Send(unsigned char* content, unsigned char num){
	while(num--){
		SBUF = *content;
		while(!TI);
		TI = 0;
		content++;
	}
}
void setUart1Buf(unsigned char* buf, unsigned char buf_num, unsigned char* head, unsigned char head_num){
	_buf = buf;
	_head = head;
	_buf_num = buf_num;
	_head_num = head_num;
}

unsigned char check_head(){
	xdata unsigned char i;
	
	for(i=0;i<_head_num;i++){
		if(_buf[i] != _head[i])return 0;
	}
	
	return 1;
}

// 串口1的中断
void UART1_Routine(void) interrupt 4{
	if(TI == 1)TI = 0;
	
	if(RI == 1){
		
		if(_buf_cursor < _buf_num){
			_buf[_buf_cursor] = SBUF;
			_buf_cursor = _buf_cursor+1;
			
			
			if(_buf_cursor>=_buf_num){ // 缓冲区满，进行判断
				_buf_cursor = 0;
				if(check_head()){
					eventID = (eventID|(1<<enumEventUart1)); // 触发事件
				}
				/*
				if((eventID&(1<<enumEventUart1)) != (1<<enumEventUart1)){ // 如果事件处理完毕，进行判断，否则不做处理
					if(check_head()){
						eventID = (eventID|(1<<enumEventUart1)); // 触发事件
					}
				}
				*/
			}
		}
		
		
		RI = 0;
	}
}