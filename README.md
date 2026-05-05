# RFID与传感器原理——实验设计

本项目为HNU物联网工程课程《RFID与传感器原理》的实验内容，具体参考`docs/整体设计.md`。

## 快速开始

**sensor-layer**

在windows系统中，使用`keil 5`编译为hex文件，然后使用`stc-isp`程序下板即可。

**connect-layer**

应用层和网络层的环境均使用uv进行管理，所以需要先保证python安装了uv：

```python
pip install uv
```

然后在目录`connect-layer`下运行`uv run main.py`即可。

**server-layer**

同样需要先保证安装uv,然后在`server-layer`目录下运行`uv run main.py`

## LICENSE

MIT LICENSE

使用代码请遵循LICENSE许可。

---

作者：物联2301 yw

2026.5.5
