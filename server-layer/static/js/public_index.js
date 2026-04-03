const API_BASE = '/api';
let currentDevice = null;
let currentPage = 1;
const pageSize = 10;
let deviceDataCount = {};

// 加载设备列表
async function loadDeviceList() {
    const deviceListEl = document.getElementById('deviceList');
    deviceListEl.innerHTML = '<div class="loading">加载中</div>';

    try {
        const response = await fetch(`${API_BASE}/get_device_list`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error('获取设备列表失败');

        const devices = await response.json();
        deviceListEl.innerHTML = '';

        if (devices.length === 0) {
            deviceListEl.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>暂无设备</p>
                </div>
            `;
            return;
        }

        // 获取每个设备的数据条数
        for (const device of devices) {
            const count = await getDeviceDataCount(device);
            deviceDataCount[device] = count;
        }

        devices.forEach(device => {
            const deviceEl = document.createElement('div');
            deviceEl.className = 'device-item';
            deviceEl.onclick = () => selectDevice(device);
            deviceEl.innerHTML = `
                <span class="device-seq">${device}</span>
            `;
            deviceListEl.appendChild(deviceEl);
        });
    } catch (error) {
        deviceListEl.innerHTML = `<div class="empty-state">❌ 加载失败：${error.message}</div>`;
    }
}

// 获取设备数据条数
async function getDeviceDataCount(deviceSeq) {
    try {
        const response = await fetch(`${API_BASE}/fetch_sensor_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_seq: deviceSeq,
                start: 0,
                num: 1
            })
        });
        if (response.ok) {
            const data = await response.json();
            return Array.isArray(data) ? data.length : 0;
        }
    } catch (e) {}
    return 0;
}

// 选择设备
function selectDevice(device) {
    currentDevice = device;
    currentPage = 1;

    document.querySelectorAll('.device-item').forEach(el => {
        el.classList.remove('active');
        if (el.querySelector('.device-seq').textContent.includes(device)) {
            el.classList.add('active');
        }
    });

    document.getElementById('selectedDevice').textContent = `当前设备：${device}`;
    loadSensorData();
}

// 加载传感器数据
async function loadSensorData() {
    if (!currentDevice) return;

    const sensorDataEl = document.getElementById('sensorData');
    sensorDataEl.innerHTML = '<div class="loading">加载中</div>';
    document.getElementById('pagination').style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/fetch_sensor_data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_seq: currentDevice,
                start: (currentPage - 1) * pageSize,
                num: pageSize
            })
        });

        if (!response.ok) throw new Error('获取数据失败');

        const data = await response.json();
        sensorDataEl.innerHTML = '';

        if (!data || data.length === 0) {
            sensorDataEl.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📉</div>
                    <p>该设备暂无传感器数据</p>
                </div>
            `;
            return;
        }

        const table = document.createElement('table');
        table.className = 'sensor-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>ID</th>
                    <th>温度 (°C)</th>
                    <th>光照</th>
                    <th>霍尔</th>
                    <th>时间戳</th>
                </tr>
            </thead>
            <tbody>
                ${data.map(row => `
                    <tr>
                        <td>${row.id}</td>
                        <td class="sensor-value">${row.temperature}</td>
                        <td class="sensor-value">${row.light}</td>
                        <td><span class="status-badge status-normal">${row.hall}</span></td>
                        <td>${formatTimestamp(row.timestamp)}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        sensorDataEl.appendChild(table);

        // 显示分页
        document.getElementById('pagination').style.display = 'flex';
        document.getElementById('pageInfo').textContent = `第 ${currentPage} 页`;
        document.getElementById('prevBtn').disabled = currentPage === 1;

        // 等待 DOM 渲染完成后滚动到表格位置
        setTimeout(() => {
            table.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

    } catch (error) {
        sensorDataEl.innerHTML = `<div class="empty-state">❌ 加载失败：${error.message}</div>`;
    }
}

// 格式化时间戳
function formatTimestamp(timestamp) {
    const date = new Date(parseFloat(timestamp) * 1000);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 分页
function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadSensorData();
    }
}

function nextPage() {
    currentPage++;
    loadSensorData();
}

// 页面加载时获取设备列表
loadDeviceList();