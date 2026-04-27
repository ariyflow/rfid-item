#include <regx52.h>
#include "rc522.h"
#include "sys.h"
#include "display.h"
#include "uart1.h"
#include "key.h"
#include "adc.h"
#include "AT24C02.h"

xdata unsigned char uid[4]; // 放置RFID的序列号
xdata unsigned char card_key[6] = {0xff,0xff,0xff,0xff,0xff,0xff}; // 验证的密钥
xdata unsigned char card_data[16]; // 临时存放读卡的数据
xdata unsigned char send_buf[24]; // 发送缓冲区（发送数据可能不等长）
xdata unsigned char receive_buf[24]; // 接收缓冲区
xdata unsigned char status = 0x0; // 临时保存状态
xdata ADC adc_data; // 保存获取的adc数据
xdata unsigned char mode = 0x00; // 当前的模式
xdata unsigned char counter_1s = 0x00; // 1s回调的计数
xdata unsigned char is_stream_led = 0; // MODE1下控制led是否流水
xdata unsigned char led_vector = 0x01; // MODE1下的下一个led状态
xdata unsigned char device_seq[6] = {0,0,0,0,0,0}; // 设备序列号
xdata unsigned char cur_device_flag = 1; // MODE0模式下控制当前显示的设备序列号（1表示前三个字节，0表示后3个字节）

code unsigned char test_data[16] = { // 测试数据
	1,2,3,4,
	5,6,7,8,
	9,10,11,12,
	13,14,15,16
};

sfr P3M1 = 0xB1;
sfr P3M0 = 0xB2;
unsigned int is_beep = 0;
void Delay100us()		//@11.0592MHz
{
	unsigned char i, j;

	_nop_();
	_nop_();
	i = 2;
	j = 15;
	do
	{
		while (--j);
	} while (--i);
}

void setBeep(unsigned int xms){
	unsigned int i=0;
	xms = xms*10;
	for(;i<xms;i++){
		P3_4 = !P3_4;
		Delay100us();
	}
}

unsigned char simple_read_uid(unsigned char* _id);
unsigned char writeRFID(unsigned char _addr, unsigned char* _data);
unsigned char readRFID(unsigned char _addr, unsigned char* _uid,unsigned char* _buf);
unsigned char read_uid(unsigned char* _id);
void commit_sensor_data();
unsigned char set_checksum(unsigned char* buf, unsigned char num); // 计算偶校验值
/*此处进入核心部分*/
void my1SCallback();
void my100msCallback();
void myKeyCallback(); // 按键回调
void myADCKeyCallback(); // ADC按键回调
void myUartCallback(); // 串口回调
void read_device_seq(); // 读取设备序列号
void my1msCallback(){
	if(is_beep){
		P3_4 = !P3_4;
		is_beep--;
	}
}

void main() {
  // unsigned char ver;
	
	sysInit();
	disInit();
	ATInit();
  uart1Init(9600);
//	P3M1 &= ~0x08;
//	P3M0 |= 0x08;
	
	setUart1Buf(receive_buf, 24, send_buf, 2);
	
	// adc初始化时，当时将p1.0和p1.1设置为了ADC引脚，导致这里错误
	// 现已解决
	adcInit(); // 暂时不能开adc的中断
	
	setCallback(enumEventInt1, my1msCallback);
	setCallback(enumEventInt100, my100msCallback);
	setCallback(enumEventKey, myKeyCallback);
	setCallback(enumEventAdcKey, myADCKeyCallback);
	setCallback(enumEventUart1, myUartCallback);
	setCallback(enumEventInt1000, my1SCallback);
	send_buf[0] = 0xaa;
	send_buf[1] = 0x55;

	read_device_seq();
	
	setLed(0x15);
	setSeg(0,1,2,3,4,5,6,7);

	rc522Init();
	// delay_ms(1000);
    
	while(1) {
			// ver = ReadRawRC(VersionReg);
			// uart1Send(&ver, 1);
			sysRun();
    }
}

// 正确返回0010 1111 = 0x2f
// 只需要传入_addr，_uid和_buf会保存RFID的uid和读取到的数据
unsigned char readRFID(unsigned char _addr, unsigned char* _uid,unsigned char* _buf){ // 尝试读取uid位于addr的数据
	xdata unsigned char tmp = 0x00, try_cnt = 10;
	while(1){
		if(PcdRequest(0x52, _uid) == 0)tmp |= (1<<0);// 寻卡 S50是0x0400

		if(PcdAnticoll(_uid) == 0)tmp |= (1<<1); // 防冲突，返回uid

		if(PcdSelect(_uid) == 0) tmp |= (1<<2); // 选卡，选择UID对应的卡片

		if(PcdAuthState(0x61, _addr, card_key, _uid) == 0) tmp |= (1<<3);

		// if(PcdWrite(_addr, test_data) == 0) status |= (1<<4);

		if(PcdRead(_addr, _buf) == 0) tmp |= (1<<5);
		
		if(tmp == 0x2f) break;
		else{ // 未成功
			if(try_cnt-- == 0) break; // 尝试10次后，直接返回
			else tmp = 0; // 再次尝试
		}
	}

	
	PcdHalt();
	return tmp;
}

// 简单获取uid，成功返回0000 0011 = 0x03
unsigned char simple_read_uid(unsigned char* _id){
	xdata unsigned char tmp = 0x00, try_cnt = 10;
	
	while(1){
		if(PcdRequest(0x52, 0x0400) == 0)tmp |= (1<<0);// 寻卡 S50是0x0400
		if(PcdAnticoll(_id) == 0)tmp |= (1<<1); // 防冲突，返回uid
		
		if(tmp == 0x03) break;
		else{ // 未成功
			if(try_cnt-- == 0) break; // 尝试10次后，直接返回
			else tmp = 0; // 再次尝试
		}
	}
	return tmp;
}

// 向地址_addr写入_data
// 成功返回0001 1111=0x1F
unsigned char writeRFID(unsigned char _addr, unsigned char* _data){
	xdata unsigned char tmp = 0x00, try_cnt = 10;
	xdata unsigned char _uid[4];
	while(1){
		if(PcdRequest(0x52, _uid) == 0)tmp |= (1<<0);// 寻卡 S50是0x0400

		if(PcdAnticoll(_uid) == 0)tmp |= (1<<1); // 防冲突，返回uid

		if(PcdSelect(_uid) == 0) tmp |= (1<<2); // 选卡，选择UID对应的卡片

		if(PcdAuthState(0x61, _addr, card_key, _uid) == 0) tmp |= (1<<3);

		if(PcdWrite(_addr, _data) == 0) tmp |= (1<<4);

		// if(PcdRead(_addr, _buf) == 0) tmp |= (1<<5);
		
		if(tmp == 0x1f) break;
		else{ // 未成功
			if(try_cnt-- == 0) break; // 尝试10次后，直接返回
			else tmp = 0; // 再次尝试
		}
	}
	PcdHalt();
	return tmp;
}

// 获取当前RFID的序列号，保存到参数_id中
// 返回值为0000 0111 = 0x07表示正确
unsigned char read_uid(unsigned char* _id){
	xdata unsigned char tmp = 0x00, try_cnt = 10;
	
	while(1){
		if(PcdRequest(0x52, 0x0400) == 0)tmp |= (1<<0);// 寻卡 S50是0x0400

		if(PcdAnticoll(_id) == 0)tmp |= (1<<1); // 防冲突，返回uid
		
		// 要获取uid，其实不需要这一步，但是为了停机，先选卡
		if(PcdSelect(_id) == 0) tmp |= (1<<2); // 选卡，选择UID对应的卡片
		
		if(tmp == 0x07) break;
		else{ // 未成功
			if(try_cnt-- == 0) break; // 尝试10次后，直接返回
			else tmp = 0; // 再次尝试
		}
	}
	PcdHalt();
	return tmp;
}

void read_device_seq(){
	unsigned char i;
	for(i=0;i<6;i++){
		device_seq[i] = rAT(0x50+i);
	}
}

void write_device_seq(unsigned char* tmp){
	unsigned char i;
	for(i=0;i<6;i++){
		wAT(0x50+i, tmp[i]);
	}
}

// 计算buf数组的偶校验结果值
unsigned char set_checksum(unsigned char* buf, unsigned char num){
	xdata unsigned char i;
	xdata unsigned char tmp = 0x00;
	for(i=0;i<num;i++){
		tmp ^= buf[i];
	}
	return tmp;
}

void commit_sensor_data(){
	adc_data = getAdc();
	
	send_buf[2]=0x08;
	send_buf[3]=0x03;
	send_buf[4]=(adc_data.adcTem>>8); // 温度
	send_buf[5]=(adc_data.adcTem&0xff);
	send_buf[6]=(adc_data.adcLum>>8); // 光照
	send_buf[7]=(adc_data.adcLum&0xff);
	send_buf[8]=(adc_data.adcHall); // 霍尔
	send_buf[9]=0; // 振动
	send_buf[10]=set_checksum(send_buf, 10);
	uart1Send(send_buf, 11);

}

void my1SCallback(){
	if(++counter_1s == 30)counter_1s = 0;

	if(mode == 1){ // 检测模式

		// 检测当前是否存在RFID
		if(simple_read_uid(uid) == 0x03){
			is_stream_led = 1;
			
			// 存在RFID时，需要上报刷卡数据
			send_buf[2] = 0x06;
			send_buf[3] = 0x06;
			send_buf[4] = uid[0];
			send_buf[5] = uid[1];
			send_buf[6] = uid[2];
			send_buf[7] = uid[3];
			send_buf[8] = set_checksum(send_buf, 8);
			uart1Send(send_buf, 9);
		}
		else is_stream_led = 0;

		if(counter_1s == 0){ // 30s发送一次
			commit_sensor_data();
		}
	}
}

void my100msCallback(){
	if(mode == 0){
		if(cur_device_flag){
			setLed(0x38); // 00111000
			setSeg(device_seq[0]>>4,device_seq[0]&0x0f,54,device_seq[1]>>4,device_seq[1]&0x0f,54,device_seq[2]>>4,device_seq[2]&0x0f);
		}
		else{
			setLed(0x07); // 00000111
			setSeg(device_seq[3]>>4,device_seq[3]&0x0f,54,device_seq[4]>>4,device_seq[4]&0x0f,54,device_seq[5]>>4,device_seq[5]&0x0f);
		}
	}
	if(mode == 1){
		if(is_stream_led){
			setLed(led_vector);
			setSeg(uid[0]>>4,uid[0]&0x0f, uid[1]>>4,uid[1]&0x0f, uid[2]>>4,uid[2]&0x0f, uid[3]>>4,uid[3]&0x0f);
			led_vector = (led_vector<<1)+(led_vector>>7);
		}
		else{
			setLed(0x00);
			setNum(0);
		}
	}
}

void myUartCallback(){
	// 串口收到数据固定为24字节，第2字节固定为指令字节
	xdata unsigned char command = 0xff; // 指令字节
	xdata unsigned char write_addr = 0x00; // 要写入数据的地址
	
	// mode0下回显所有信息
	// if (mode == 0){
	// 	uart1Send(receive_buf, 24);
	// 	return;
	// }


	// 收到数据后，首先进行偶校验判断
	if(receive_buf[23] != set_checksum(receive_buf, 23)) return;
	
	command = receive_buf[2];
	if(command == 0x00){
		// 00 - 发送序列号，2固定为6，3固定为0，4-7为4字节序列号，8为偶校验
		// 包头2+字节数1+指令字节1+序列号4+偶校验1=9
		
		// uart1Send(send_buf, 2);
		if(read_uid(uid)!=0x07){ // 失败，发送DEBUG数据帧，告知失败
			send_buf[2] = 1;
			send_buf[3] = 0xFF;
			send_buf[4] = 0x02;
			send_buf[5] = set_checksum(send_buf, 5);
			uart1Send(send_buf, 6);
			return;
		}
		// uart1Send(uid, 4);
		
		send_buf[2] = 6;
		send_buf[3] = 0;
		send_buf[4] = uid[0];
		send_buf[5] = uid[1];
		send_buf[6] = uid[2];
		send_buf[7] = uid[3];
		send_buf[8] = set_checksum(send_buf, 8);

		uart1Send(send_buf, 9);
	}
	else if(command == 0x01){
		// 01 - 获取某个地址的值（这里假设获取0x20，数据为1-16）
		// 2固定为0x13，3固定为01，4为地址（0x20），5-20为数据，21为偶校验
		// 包头2+数据字节1+指令字节1+读取地址1+数据16+偶校验1=22
		send_buf[2]=0x13;
		send_buf[3]=0x01;
		send_buf[4]=receive_buf[3]; // 读取地址
		
		if(readRFID(receive_buf[3], uid, card_data) != 0x2F){
			send_buf[2] = 3; // 返回失败帧
			send_buf[3] = 0xFF;
			send_buf[4] = 0x01;
			send_buf[5] = set_checksum(send_buf, 5);
			uart1Send(send_buf, 6);
			return;
		}
		
		send_buf[5]=card_data[0];
		send_buf[6]=card_data[1];
		send_buf[7]=card_data[2];
		send_buf[8]=card_data[3];
		send_buf[9]=card_data[4];
		send_buf[10]=card_data[5];
		send_buf[11]=card_data[6];
		send_buf[12]=card_data[7];
		send_buf[13]=card_data[8];
		send_buf[14]=card_data[9];
		send_buf[15]=card_data[10];
		send_buf[16]=card_data[11];
		send_buf[17]=card_data[12];
		send_buf[18]=card_data[13];
		send_buf[19]=card_data[14];
		send_buf[20]=card_data[15];
		send_buf[21]=set_checksum(send_buf, 21);
		uart1Send(send_buf, 22);
	}
	else if(command == 0x02){
		// 02 - 写入某个地址数据，这条指令需要分开处理，这里是成功写入地址0x20的测试
		// 2固定0x13, 3固定0x02, 4固定0x01(成功), 5-20为数据，21为偶校验
		// 包头2+数据字节1+指令字节1+返回状态1+数据16+偶校验1=22
		
		if(writeRFID(receive_buf[3], &receive_buf[4]) != 0x1f){
			// 写入失败只发送DEBUG数据，不发送协议规定的数据包了
			send_buf[2] = 3;
			send_buf[3] = 0xFF;
			send_buf[4] = 3;
			send_buf[5] = set_checksum(send_buf, 5);
			uart1Send(send_buf, 6);
			return;
		}

		send_buf[2]=0x13;
		send_buf[3]=0x02;
		send_buf[4]=0x01;
		send_buf[5]=receive_buf[4];
		send_buf[6]=receive_buf[5];
		send_buf[7]=receive_buf[6];
		send_buf[8]=receive_buf[7];
		send_buf[9]=receive_buf[8];
		send_buf[10]=receive_buf[9];
		send_buf[11]=receive_buf[10];
		send_buf[12]=receive_buf[11];
		send_buf[13]=receive_buf[12];
		send_buf[14]=receive_buf[13];
		send_buf[15]=receive_buf[14];
		send_buf[16]=receive_buf[15];
		send_buf[17]=receive_buf[16];
		send_buf[18]=receive_buf[17];
		send_buf[19]=receive_buf[18];
		send_buf[20]=receive_buf[19];
		send_buf[21]=set_checksum(send_buf, 21);
		uart1Send(send_buf, 22);
	}
	else if(command == 0x03){
		// 03 - 获取传感器数据，此时传输传感器数据即可
		// 包头2+数据字节1+指令字节1+温度2+光照2+霍尔1+振动1+偶校验1=11
		
		commit_sensor_data();
	}
	else if(command == 0x04){
		/* 04 - 设置从机序列号，此时需要设置从机序号为receive_buf[3:9]
		成功时返回：
			aa 55 08 04 receive_buf[3:9] chk_sum
		失败时返回：(其实失败了也检查不出来，所以不会返回失败的数据帧，写入失败应该会返回一个无效帧，可以在log中查看)
			aa 55 03 04 00 chk_sum
		
		*/
		
		write_device_seq(&receive_buf[3]);
		// wAT(0x50, receive_buf[3]);
		// wAT(0x51, receive_buf[4]);
		// wAT(0x52, receive_buf[5]);
		// wAT(0x53, receive_buf[6]);
		// wAT(0x54, receive_buf[7]);
		// wAT(0x55, receive_buf[8]);

		read_device_seq(); // 验证正确性，再读一次

		send_buf[2] = 0x08;
		send_buf[3] = 0x04;
		send_buf[4] = device_seq[0];
		send_buf[5] = device_seq[1];
		send_buf[6] = device_seq[2];
		send_buf[7] = device_seq[3];
		send_buf[8] = device_seq[4];
		send_buf[9] = device_seq[5];
		send_buf[10] = set_checksum(send_buf, 10);

		uart1Send(send_buf, 11);
	}
	else if(command == 0x05){
		/*
		05 - 获取从机序列号，从AT24C02获取序列号并返回。
		*/
		send_buf[2] = 0x08;
		send_buf[3] = 0x05;
		send_buf[4] = device_seq[0];
		send_buf[5] = device_seq[1];
		send_buf[6] = device_seq[2];
		send_buf[7] = device_seq[3];
		send_buf[8] = device_seq[4];
		send_buf[9] = device_seq[5];
		send_buf[10] = set_checksum(send_buf, 10);

		uart1Send(send_buf, 11);

	}
	else if(command == 0x06){
		// 收到刷卡的响应
		if(receive_buf[3] == 0x01){ // 成功
			setBeep(200);
			send_buf[2] = 0x03;
			send_buf[3] = 0xFF;
			send_buf[4] = 0x06;
			send_buf[5] = set_checksum(send_buf, 5);
			uart1Send(send_buf, 6);
		}
	}
}

void myADCKeyCallback(){
	xdata unsigned char key;

	if(mode == 0){ // MODE0 待机模式
		
		key = getADCKeyAct(enumADCKey3);
		// setLed(key);
		if(key == enumKeyPress){ // key3按下，返回RFID序列号和地址20的数据
			
			// 返回序列号和地址20的数据
			status = readRFID(20, uid, card_data);
			if(status != 0x2F){ // 失败返回状态码
				send_buf[2] = status;
				uart1Send(send_buf, 3);
			}
			else{
				uart1Send(uid, 4);
				uart1Send(card_data, 16);
			}
			// do {
			// 	status = readRFID(20, uid, card_data);
			// }
			// while(status != 0x2f);
			// uart1Send(uid, 4);
			// uart1Send(card_data, 16);
		}

		key = getADCKeyAct(enumADCKeyCenter);
		if(key == enumKeyPress){
			xdata unsigned char tmp_data[6] = {0,0,0,0,0,0};
			write_device_seq(tmp_data);
			read_device_seq();
			// 向地址20写入数据
			// send_buf[2] = writeRFID(20, test_data);
			// uart1Send(send_buf, 3);
		}

		key = getADCKeyAct(enumADCKeyUp);
		if(key == enumKeyPress){
			// commit_sensor_data();
			cur_device_flag = 1 - cur_device_flag;
		}

		key = getADCKeyAct(enumADCKeyDown);
		if(key == enumKeyPress){
			cur_device_flag = 1 - cur_device_flag;
		}
	}

	// key = getADCKeyAct(enumADCKeyUp);
	// if(key == enumKeyPress){

	// }
	// key = getADCKeyAct(enumADCKeyDown);
	// if(key == enumKeyPress){

	// }
	// key = getADCKeyAct(enumADCKeyLeft);
	// if(key == enumKeyPress){
	// 	// 写入失败，返回失败的数据帧
	// 	// 包头2+数据字节1+指令字节1+返回状态1+偶校验1=6
	// 	send_buf[2]=0x03;
	// 	send_buf[3]=0x02;
	// 	send_buf[4]=0x00;
	// 	send_buf[5]=set_checksum(send_buf, 5);
	// 	uart1Send(send_buf, 6);
	// }
	// key = getADCKeyAct(enumADCKeyRight);
	// if(key == enumKeyPress){

	// }
	
}

void myKeyCallback(){
	xdata unsigned char key;

	// key2是模式切换键，与其余逻辑分离
	key = getKeyAct(enumKey2);
	if(key == enumKeyPress){ // key2按下，切换模式
		// 切换前的操作

		mode = (mode+1)%3;

		// 切换后的操作
		if(mode == 0){
			setNum(1234567);
		}
		else if(mode == 1){
			setLed(0x00);
			setNum(0);
		}
		else if(mode == 2){
			setNum(2);
		}
	}

	if(mode == 0){ // MODE0 待机模式
		key = getKeyAct(enumKey1);
		if(key == enumKeyPress){ // key1 按下，获取RFID序列号
			// WriteRawRC(CommandReg,PCD_RESETPHASE);

	//		send_buf[0] = ReadRawRC(CommandReg);
	//		send_buf[1] = ReadRawRC(ModeReg);
	//		send_buf[2] = ReadRawRC(TReloadRegL);
	//		send_buf[3] = ReadRawRC(TReloadRegH);
	//		send_buf[4] = ReadRawRC(TModeReg);
	//		send_buf[5] = ReadRawRC(TPrescalerReg);
	//		send_buf[6] = ReadRawRC(TxAskReg);
	//		send_buf[7] = 0xAA;
	//		uart1Send(send_buf, 8);
	//		setLed(0xa3);

			// 获取uid
			if(read_uid(uid)!=0x07)return;
			uart1Send(uid, 4);
		}
		// ReadCardData(uid, card_buf);

	}

}
