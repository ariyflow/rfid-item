#include "ir.h"
#include <intrins.h>
#include "regx52.h"
#include "regdef.h"
#include "uart1.h"
#include "display.h"

#ifndef NULL
#define NULL ((void*)(0))
#endif

sbit IR_TX = P3^5;
sbit IR_RX = P3^6;
sfr P3M1 = 0xB1;
sfr P3M0 = 0xB2;

// === 发送部分（阻塞式，不依赖中断）===
static void delay_us(uint16_t us) {
    // 11.0592MHz, 12T mode: 1us ≈ 11 cycles → 粗略延时
    while (us--) {
        _nop_(); _nop_(); _nop_(); _nop_();
        _nop_(); _nop_(); _nop_(); _nop_();
        _nop_(); _nop_(); _nop_();
    }
}

static void send_carrier_us(uint16_t time_us) {
    // 38kHz: 周期 ≈ 26.3us → 高13us + 低13us
    uint16_t count = time_us / 26;
		uint16_t i;
    for (i = 0; i < count; i++) {
        IR_TX = 1;
        delay_us(13);
        IR_TX = 0;
        delay_us(13);
    }
}

void IR_SendNEC(unsigned char addr, unsigned char cmd) {
	// 临时关闭中断（可选，防止发送被干扰）
	unsigned char ea_save = EA;
	// 构造32位数据：ADDR, ~ADDR, CMD, ~CMD
	unsigned char frame[4];
	uint8_t b;
	int i;
	
	frame[0] = addr;
	frame[1] = ~addr;
	frame[2] = cmd;
	frame[3] = ~cmd;
	
	EA = 0;

	// 引导码
	send_carrier_us(9000);
	delay_us(4500);

	

	// 发送32位
	for (i = 0; i < 32; i++) {
			b = (frame[i / 8] >> (7 - (i % 8))) & 1;
			send_carrier_us(560);
			if (b) {
					delay_us(1690);
			} else {
					delay_us(560);
			}
	}

	IR_TX = 0;
	EA = ea_save;
}

// === 接收部分（状态机 + 1ms 轮询）===
static ir_recv_callback_t g_recv_callback = NULL;

// 接收状态
#define IR_STATE_IDLE       0
#define IR_STATE_HEADER     1
#define IR_STATE_DATA       2
#define IR_STATE_ERROR      3

static uint8_t  ir_state = IR_STATE_IDLE;
static uint16_t ir_low_time = 0;   // 当前低电平持续时间（单位：1ms）
static uint16_t ir_high_time = 0;  // 上一次高电平持续时间（用于判断引导码）
static uint8_t  ir_data[4];        // 接收缓冲
static uint8_t  ir_bit_count = 0;

void IR_Init(void) {
    // P3.5: 推挽输出（发送）
    P3M0 |= 0x20; P3M1 &= ~0x20;
    IR_TX = 0;

    // P3.6: 高阻输入（接收，需外部上拉，你的电路已有 R42=10k）
    P3M0 &= ~0x40; P3M1 |= 0x40;

    ir_state = IR_STATE_IDLE;
    g_recv_callback = NULL;
}

extern xdata unsigned char send_buf[8];
extern void setBuf(unsigned char s0,unsigned char s1,unsigned char s2,unsigned char s3,unsigned char s4,unsigned char s5,unsigned char s6,unsigned char s7);

void IR_Poll(void) {
    static uint8_t last_rx = 1;

    uint8_t current_rx = IR_RX;
	
		uint8_t byte_idx;
		uint8_t bit_idx;

		
    if (last_rx == 1 && current_rx == 0) {
			
        // 下降沿：高电平结束
        // 此时 ir_high_time 是刚刚结束的高电平持续时间
        if (ir_state == IR_STATE_IDLE) {
            // 检测引导码高电平：应≈9ms
            if (ir_high_time >= 8 && ir_high_time <= 10) {
                ir_state = IR_STATE_HEADER;
                ir_low_time = 0;
                ir_bit_count = 0;
            } else {
                ir_state = IR_STATE_IDLE;
            }
        } else if (ir_state == IR_STATE_DATA) {
            // 数据位高电平固定为 560us ≈ 0~1ms，这里忽略（因精度限制）
            // 我们主要靠低电平宽度判断 0/1
        }
        // 重置高电平计时
        ir_high_time = 0;
    } else if (last_rx == 0 && current_rx == 1) {
        // 上升沿：低电平结束
				setSeg(1,2,3,4,5,6,7,8);
        if (ir_state == IR_STATE_HEADER) {
					
            // 判断引导码低电平：应≈4.5ms
            if (ir_low_time >= 4 && ir_low_time <= 5) {
							
                ir_state = IR_STATE_DATA;
            } else {
							
                ir_state = IR_STATE_IDLE;
            }
        } else if (ir_state == IR_STATE_DATA) {
            // 解析数据位
					
            uint8_t bit_val;
					
            if (ir_low_time >= 1 && ir_low_time <= 2) {
                bit_val = 0; // 560us 低
            } else if (ir_low_time >= 2 && ir_low_time <= 6) {
                bit_val = 1; // 1690us 低
            } else {
                ir_state = IR_STATE_IDLE;
                last_rx = current_rx;
                return;
            }

            // 存入数据
            byte_idx = ir_bit_count / 8;
            bit_idx = 7 - (ir_bit_count % 8);
            if (byte_idx < 4) {
                if (bit_val) ir_data[byte_idx] |= (1 << bit_idx);
                else         ir_data[byte_idx] &= ~(1 << bit_idx);
            }
            ir_bit_count++;
						

						
            if (ir_bit_count == 32) {
                // 校验
                if (ir_data[0] == (uint8_t)~ir_data[1] &&
                    ir_data[2] == (uint8_t)~ir_data[3]) {
											
                    if (g_recv_callback) {

                        g_recv_callback(ir_data[0], ir_data[2]);
                    }
                }
                ir_state = IR_STATE_IDLE;
            }
        }
        ir_low_time = 0;
    }

    // 更新电平持续时间（每 1ms）
    if (current_rx == 0) {
        ir_low_time++;
    } else {
        ir_high_time++;
    }

    // 超时保护
    if (ir_state != IR_STATE_IDLE) {
        if ((ir_state == IR_STATE_HEADER && ir_low_time > 10) ||
            (ir_state == IR_STATE_DATA  && (ir_low_time > 10 || ir_high_time > 10))) {
            ir_state = IR_STATE_IDLE;
        }
    }

    last_rx = current_rx;
}

void IR_SetRecvCallback(ir_recv_callback_t callback) {
    g_recv_callback = callback;
}