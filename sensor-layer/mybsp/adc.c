#include <adc.h>
#include <key.h>

xdata unsigned char _adc_turn = 0; // 当前获取的adc索引
xdata ADC _adc; // 保存adc的值
xdata unsigned char _adckeyPress = 0; // 保存adc按键是否按下
xdata unsigned char _key3cnt=0,_rightcnt=0,_downcnt=0,_centercnt=0,_leftcnt=0,_upcnt=0;
xdata unsigned int _center_win;

extern xdata unsigned int eventID;
void adcInit(){
	P1ASF = 0x9c;
	ADC_CONTR = 0x88; // 低三位控制数模转换的位置
	
	EADC = 1; // 开启中断
	EA = 1;
}

ADC getAdc(){
	return _adc;
}

unsigned char getADCKeyAct(unsigned char key){
	if(key == enumADCKey3) {return (_adckeyPress&0x01);}
	else if(key == enumADCKeyRight) return ((_adckeyPress&0x02)>>1);
	else if(key == enumADCKeyDown) return ((_adckeyPress&0x04)>>2);
	else if(key == enumADCKeyCenter) return ((_adckeyPress&0x08)>>3);
	else if(key == enumADCKeyLeft) return ((_adckeyPress&0x10)>>4);
	else if(key == enumADCKeyUp) return ((_adckeyPress&0x20)>>5);
	else return 0;
}

void ADC_Routine(void) interrupt 5{
	if(_adc_turn == 0){
		_adc.adcP0 = (ADC_RES<<2)+ADC_RESL;
	}
	else if(_adc_turn == 1){
		_adc.adcP1 = (ADC_RES<<2)+ADC_RESL;
	}
	else if(_adc_turn == 2){
		_adc.adcHall = (ADC_RES<<2)+ADC_RESL;
	}
	else if(_adc_turn == 3){
		_adc.adcTem = (ADC_RES<<2)+ADC_RESL;
	}
	else if(_adc_turn == 4){
		_adc.adcLum = (ADC_RES<<2)+ADC_RESL;
	}
	else if(_adc_turn == 7){ // 这里需要判断是否有按键按下
		_adc.adcNav = (ADC_RES<<2)+ADC_RESL;
		
		if(_adc.adcNav>=0x00 && _adc.adcNav<=0x10){
			if(_key3cnt == 20){_adckeyPress = (_adckeyPress|0x01); eventID = (eventID | (1 << enumEventAdcKey)); ++_key3cnt;}
			else if(_key3cnt < 20)++_key3cnt;
		}
		else _key3cnt = 0;
		
		if(_adc.adcNav>=0x8b && _adc.adcNav<=0xab){
			if(_rightcnt==20){_adckeyPress = (_adckeyPress|0x02); eventID = (eventID | (1 << enumEventAdcKey));_rightcnt = _rightcnt+1;}
			else if(_rightcnt<20)++_rightcnt;
		}
		else _rightcnt = 0;
		
		if(_adc.adcNav>=0x120 && _adc.adcNav<=0x140){
			
			if(_downcnt==20){_adckeyPress = (_adckeyPress|0x04); eventID = (eventID | (1 << enumEventAdcKey)); _downcnt = _downcnt+1;}
			else if(_downcnt<20)++_downcnt;
		}
		else _downcnt = 0;
		
//		if(_adc.adcNav>=0x1b9 && _adc.adcNav<=0x1d9){
//			
//			if(_centercnt==20){_adckeyPress = (_adckeyPress|0x08); eventID = (eventID | (1 << enumEventAdcKey)); _centercnt = _centercnt+1;}
//			else if(_centercnt < 20)++_centercnt;
//		}
//		else _centercnt = 0;
		
		_center_win = ((_center_win<<1)|(_adc.adcNav>=0x1b9 && _adc.adcNav<=0x1d9)); // 滑动窗口
		if(_center_win == 0xe000){
			_adckeyPress = (_adckeyPress|0x08);
			eventID = (eventID | (1 << enumEventAdcKey));
		}
		
		if(_adc.adcNav>=0x248 && _adc.adcNav<=0x268){
			if(_leftcnt==20){_adckeyPress = (_adckeyPress|0x10); eventID = (eventID | (1 << enumEventAdcKey)); _leftcnt = _leftcnt+1;}
			else if(_leftcnt < 20)++_leftcnt;
		}
		else _leftcnt = 0;
		
		if(_adc.adcNav>=0x2d3 && _adc.adcNav<=0x2f3){
			if(_upcnt==20){_adckeyPress = (_adckeyPress|0x20); eventID = (eventID | (1 << enumEventAdcKey)); _upcnt = _upcnt+1;}
			else if(_upcnt < 20)++_upcnt;
		}
		else _upcnt = 0;
	}
	
	_adc_turn = (_adc_turn+1)%8;
	ADC_CONTR = 0x88+_adc_turn;
}