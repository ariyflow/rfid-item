#include <intrins.h>
#include <regx52.h>

#ifndef __REGDEF_H__
#define __REGDEF_H__

sfr P2M1 = 0x95; // P2的模式控制寄存器，01为推挽输出
sfr P2M0 = 0x96;
sfr P0M1 = 0x93;
sfr P0M0 = 0x94;

// ADC转换相关
sfr P1ASF = 0x9D; // P1的控制寄存器，为0xff时P1作为模拟功能A/D使用
sfr ADC_CONTR = 0xBC; // ADC控制寄存器，使用时直接赋值，不要用位运算
/*
.7 - 电源，为1时有效; 
.6.5 - 转换次数控制位，越大越快
.4 - 数模转换完成标志位，需要由软件置0（中断或者轮询）
.3 - 数模转换启动控制位，为1时开始转换，转换结束后为0
.2.1.0 - 模拟输入通道选择，为P1的索引
*/
sfr PCON2 = 0x97; // 主要使用.5(ADRj) - ADC结果位置，ADC转换值共10位，具体参照P763

sfr ADC_RES = 0xBD; // 保存adc值的两个寄存器
sfr ADC_RESL = 0xBE;

sbit EADC = 0xAD; // ADC中断的标志位

// 定时器相关
sfr AUXR = 0x8E; // 辅助寄存器，高两位控制0，1定时器的分频，最低位控制串口1使用的定时器，这里使用定时器1，所以需要置0

// SM模块相关
sfr P4 = 0xC0;
sfr P4M1 = 0xB3;
sfr P4M0 = 0xB4;

sbit P4_0 = 0xC0;
sbit P4_1 = 0xC1;
sbit P4_2 = 0xC2;
sbit P4_3 = 0xC3;
sbit P4_4 = 0xC4;
sbit P4_5 = 0xC5;
sbit P4_6 = 0xC6;
sbit P4_7 = 0xC7;

sbit S1 = 0xC1;
sbit S2 = 0xC2;
sbit S3 = 0xC3;
sbit S4 = 0xC4;

sbit KEY1 = 0xB2; // 两个按键的引脚，为0时按下
sbit KEY2 = 0xB3;

sbit PADC = 0xBD; // 开始定时器1中断后，由于adc的级别较低，中断会被覆盖，所以需要手动提到高优先级

#endif