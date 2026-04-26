# 刷卡记录查看功能设计

## 概述

在 dashboard 界面新增刷卡记录查看功能，所有登录用户均可使用。

## 功能需求

### 1. 删除"关于"界面
- 移除侧边栏"关于"菜单项
- 移除 `#about-section` 区域

### 2. 刷卡记录界面

**界面布局**
- 侧边栏菜单添加"刷卡记录"入口
- 主内容区显示刷卡记录表格和筛选控件

**筛选控件**
- 设备下拉选择器：全部设备 / 特定设备（从 `/api/get_device_list` 获取）
- 时间范围：
  - 开始日期输入框（type="date"）
  - 结束日期输入框（type="date"）
  - 最小单位为天
- 快捷按钮：最近1天、最近7天、最近30天（点击自动填充开始/结束日期）
- 查询按钮

**表格内容**
| 字段 | 说明 |
|------|------|
| 设备序列号 | device_seq |
| RFID序列号 | rfid_serial |
| 刷卡时间 | timestamp（北京时间 UTC+8，格式：YYYY-MM-DD HH:mm:ss） |

**分页**
- 每页20条记录
- 显示：当前页 / 总页数
- 上一页 / 下一页 按钮

### 3. API 接口

**提交刷卡记录**（已实现）
- `POST /api/submit_card_swipe` - 设备端调用

**查询刷卡记录**
- `POST /api/fetch_card_swipe`
- 请求参数：`{"device_seq": "AABBCCDDEEFF", "start": 0, "num": 20}`
- 响应：`{"status": "success", "swipes": [...]}`
- 注意：device_seq 为可选，空表示所有设备

### 4. 时间戳处理
- 数据库存储：Unix 时间戳（str(time.time())）
- 显示转换：前端将 Unix 时间戳转换为北京时间（UTC+8）显示
- 筛选时：前端将日期转换为 Unix 时间戳发送给后端

## 文件变更

| 文件 | 操作 |
|------|------|
| `static/html/dashboard.html` | 添加菜单项和 section，移除"关于" |
| `static/js/card-swipe.js` | 新建，刷卡记录前端逻辑 |
| `static/css/card-swipe.css` | 新建，刷卡记录样式 |

## 权限
- 所有登录用户均可使用
- 无需 root 权限
