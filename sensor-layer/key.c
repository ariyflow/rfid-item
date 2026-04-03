#include <key.h>

xdata unsigned char keyPress; // 低三位分别表示key0,key1,key2按下，按下后等待回调函数执行，执行结束后清零

unsigned char getKeyAct(unsigned char key){
	if(key == enumKey1){
		return (keyPress&0x01);
	}
	else if(key == enumKey2){
		return (keyPress&0x02)>>1;
	}
	return 0;
}