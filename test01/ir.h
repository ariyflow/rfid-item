#ifndef __IR_NEC_POLL_H__
#define __IR_NEC_POLL_H__

#define uint8_t unsigned char
#define uint16_t unsigned int

// 初始化（设置引脚等）
extern void IR_Init();

// 每 1ms 调用一次！用于接收解码
extern void IR_Poll();

// 发送 NEC 帧：addr (8bit), cmd (8bit)
extern void IR_SendNEC(unsigned char addr, unsigned char cmd);

// 设置接收回调（推荐方式）
typedef void (*ir_recv_callback_t)(uint8_t addr, uint8_t cmd);

extern void IR_SetRecvCallback(ir_recv_callback_t callback);

#endif