#ifndef __KEY_H__
#define __KEY_H__

extern unsigned char getKeyAct(unsigned char key); // 判断key是否按下

enum keyName{
	enumKey1,
	enumKey2
};

enum keyAct{
	enumKeyNULL,
	enumKeyPress
};

#endif