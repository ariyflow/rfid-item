#include <regdef.h>

xdata unsigned char _dis_turn = 0x10; // 低四位表示P2的低四位，用于设置显示位置
xdata unsigned char _dis_shape; //显示的形状，将会赋值给P0
xdata unsigned char _seg_shape[8]; // 保存数码管显示的形状
code unsigned char _dis_table[] = { 
    0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, // 0-7
//  0(0)  1(1)  2(2)  3(3)  4(4)  5(5)  6(6)  7(7)
    0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71, // 8-15
//  8(8)  9(9)  a(10) b(11) c(12) d(13) e(14) f(15)
    0xBF, 0x86, 0xDB, 0xcF, 0xE6, 0xED, 0xFD, 0x87, // 16-23
//  0.(16)1.(17)2.(18)3.(19)4.(20)5.(21)6.(22)7.(23)
    0xFF, 0xEF, 0x3d, 0x76, 0x0f, 0x0E, 0x75, 0x38, // 24-31
//  8.(24)9.(25)G(26) H(27) I(28) J(29) K(30) L(31)
    0x37, 0x54, 0x5c, 0x73, 0x67, 0x31, 0x49, 0x78, // 32-39
//  M(32) N(33) O(34) P(35) Q(36) R(37) S(38) T(39)
    0x3e, 0x1c, 0x7e, 0x64, 0x6e, 0x5a, 0x00, 0xFF,  // 40-47
//  U(40) V(41) W(42) X(43) Y(44) Z(45) None  ALL
		0xf7, 0xfc, 0xb9, 0xde, 0xf9, 0xf1, 0x40
//  A.(48)B.(49)C.(50)D.(51)E.(52)F.(53) -(54)
};

void disInit(){
	// 设置推挽输出
	P2M1 = 0x00;
	P2M0 = 0xff;
	P0M1 = 0x00;
	P0M0 = 0xff;
}

void setLed(char led_vector){
	_dis_shape = led_vector;
}

void setSeg(char s0, char s1, char s2, char s3, char s4, char s5, char s6, char s7){
	_seg_shape[0] = _dis_table[s0];
	_seg_shape[1] = _dis_table[s1];
	_seg_shape[2] = _dis_table[s2];
	_seg_shape[3] = _dis_table[s3];
	_seg_shape[4] = _dis_table[s4];
	_seg_shape[5] = _dis_table[s5];
	_seg_shape[6] = _dis_table[s6];
	_seg_shape[7] = _dis_table[s7];
}

void setNum(unsigned long num){
	_seg_shape[0] = _dis_table[num/10000000%10];
	_seg_shape[1] = _dis_table[num/1000000%10];
	_seg_shape[2] = _dis_table[num/100000%10];
	_seg_shape[3] = _dis_table[num/10000%10];
	_seg_shape[4] = _dis_table[num/1000%10];
	_seg_shape[5] = _dis_table[num/100%10];
	_seg_shape[6] = _dis_table[num/10%10];
	_seg_shape[7] = _dis_table[num%10];
}

void addPoint(unsigned char cur){
	_seg_shape[cur] += 0x80;
}

void disRun(){
	// if((dis_turn & 0x10) != 0x10)return;
	
	if((_dis_turn&0x08) == 0x08){ // 显示led
		P2 = (P2&0xf7)+0x08;
		P0 = _dis_shape;
		_dis_turn = 0x00;
	}
	else{ // 显示数码管
		P2 = (P2&0xf0)+(_dis_turn&0x07);
		P0 = _seg_shape[(_dis_turn&0x07)];
		_dis_turn = ((_dis_turn + 1)&0x0f);
	}
	
}