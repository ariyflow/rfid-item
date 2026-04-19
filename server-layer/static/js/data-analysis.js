// 数据分析页面 JavaScript 逻辑

document.addEventListener('DOMContentLoaded', () => {
    const settingsSection = document.getElementById('settings-section');
    if (!settingsSection) {
        return;
    }

    const state = {
        currentTab: 'single-device',
        singleDeviceChart: null,
        lightSingleChart: null,
        globalTempChart: null,
        globalLightChart: null,
    };

    const deviceColors = [
        { border: 'rgb(255, 99, 132)', bg: 'rgba(255, 99, 132, 0.1)' },
        { border: 'rgb(54, 162, 235)', bg: 'rgba(54, 162, 235, 0.1)' },
        { border: 'rgb(75, 192, 192)', bg: 'rgba(75, 192, 192, 0.1)' },
        { border: 'rgb(255, 206, 86)', bg: 'rgba(255, 206, 86, 0.1)' },
        { border: 'rgb(153, 102, 255)', bg: 'rgba(153, 102, 255, 0.1)' },
        { border: 'rgb(255, 159, 64)', bg: 'rgba(255, 159, 64, 0.1)' },
        { border: 'rgb(199, 199, 199)', bg: 'rgba(199, 199, 199, 0.1)' },
        { border: 'rgb(83, 102, 255)', bg: 'rgba(83, 102, 255, 0.1)' },
    ];

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    async function parseJsonSafe(response) {
        try {
            return await response.json();
        } catch (_) {
            return null;
        }
    }

    function showLoginModal() {
        const modal = document.getElementById('login-modal');
        if (modal) modal.style.display = 'flex';
    }

    async function getDeviceList() {
        // 优先使用 device-management.js 已缓存的设备列表
        if (window._cachedDeviceList) {
            return window._cachedDeviceList;
        }
        const response = await fetch('/api/get_device_list', { method: 'GET' });
        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }
        const payload = await parseJsonSafe(response);
        if (!response.ok) {
            throw new Error(payload?.message || '获取设备列表失败');
        }
        const list = Array.isArray(payload) ? payload : [];
        window._cachedDeviceList = list;
        return list;
    }

    async function fetchAnalysisData(deviceSeq, startTime, endTime, limit) {
        const body = {
            start_time: String(startTime),
            end_time: String(endTime),
            limit: limit,
        };
        if (deviceSeq) {
            body.device_seq = deviceSeq;
        }

        const response = await fetch('/dashboard/fetch_analysis_data', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }

        const payload = await parseJsonSafe(response);
        if (!response.ok) {
            throw new Error(payload?.message || '获取分析数据失败');
        }
        return payload;
    }

    function formatTimestamp(rawTimestamp) {
        const num = Number(rawTimestamp);
        if (Number.isNaN(num)) {
            return rawTimestamp;
        }
        const date = new Date(num * 1000);
        if (Number.isNaN(date.getTime())) {
            return rawTimestamp;
        }
        return date.toLocaleString('zh-CN', {
            hour12: false,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    }

    function createOrUpdateLineChart(canvasId, labels, datasets, yAxisLabel) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            return null;
        }

        if (Chart.getChart(ctx)) {
            Chart.getChart(ctx).destroy();
        }

        return new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: {
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.datasets.map((dataset, i) => ({
                                        text: dataset.label,
                                        fillStyle: dataset.backgroundColor,
                                        strokeStyle: dataset.borderColor,
                                        lineWidth: 2,
                                        hidden: !chart.getDatasetMeta(i).visible,
                                        index: i,
                                    }));
                                }
                                return [];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '时间',
                        },
                        ticks: {
                            maxTicksLimit: 10,
                        },
                    },
                    y: {
                        title: {
                            display: true,
                            text: yAxisLabel,
                        },
                    },
                },
            },
        });
    }

    function renderSingleDeviceCharts(data) {
        if (!data || !data.length) {
            const emptyLabels = ['无数据'];
            createOrUpdateLineChart(
                'temperature-chart-single',
                emptyLabels,
                [{
                    label: '温度 (°C)',
                    data: [null],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.3,
                    fill: true,
                }],
                '温度 (°C)'
            );
            createOrUpdateLineChart(
                'light-chart-single',
                emptyLabels,
                [{
                    label: '光强',
                    data: [null],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.3,
                    fill: true,
                }],
                '光强'
            );
            return;
        }

        const labels = data.map(item => formatTimestamp(item.timestamp));
        const temperatures = data.map(item => item.temperature ?? null);
        const lights = data.map(item => item.light ?? null);

        createOrUpdateLineChart(
            'temperature-chart-single',
            labels,
            [{
                label: '温度 (°C)',
                data: temperatures,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.3,
                fill: true,
            }],
            '温度 (°C)'
        );

        createOrUpdateLineChart(
            'light-chart-single',
            labels,
            [{
                label: '光强',
                data: lights,
                borderColor: 'rgb(54, 162, 235)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.3,
                fill: true,
            }],
            '光强'
        );
    }

    function renderGlobalCharts(data) {
        if (!data || !data.length) {
            const emptyLabels = ['无数据'];
            createOrUpdateLineChart(
                'temperature-chart-global',
                emptyLabels,
                [{
                    label: '温度 (°C)',
                    data: [null],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.3,
                    fill: true,
                }],
                '温度 (°C)'
            );
            createOrUpdateLineChart(
                'light-chart-global',
                emptyLabels,
                [{
                    label: '光强',
                    data: [null],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.3,
                    fill: true,
                }],
                '光强'
            );
            return;
        }

        const deviceSeqs = [...new Set(data.map(item => item.device_seq))];
        const labelSet = new Set();
        data.forEach(item => labelSet.add(formatTimestamp(item.timestamp)));
        const labels = [...labelSet];

        const tempDatasets = deviceSeqs.map((seq, idx) => {
            const colorIdx = idx % deviceColors.length;
            const color = deviceColors[colorIdx];
            const seqData = data.filter(item => item.device_seq === seq);
            const dataMap = {};
            seqData.forEach(item => {
                dataMap[formatTimestamp(item.timestamp)] = item.temperature;
            });
            return {
                label: `${escapeHtml(seq)} - 温度`,
                data: labels.map(label => dataMap[label] ?? null),
                borderColor: color.border,
                backgroundColor: color.bg,
                tension: 0.3,
                fill: false,
            };
        });

        const lightDatasets = deviceSeqs.map((seq, idx) => {
            const colorIdx = idx % deviceColors.length;
            const color = deviceColors[colorIdx];
            const seqData = data.filter(item => item.device_seq === seq);
            const dataMap = {};
            seqData.forEach(item => {
                dataMap[formatTimestamp(item.timestamp)] = item.light;
            });
            return {
                label: `${escapeHtml(seq)} - 光强`,
                data: labels.map(label => dataMap[label] ?? null),
                borderColor: color.border,
                backgroundColor: color.bg,
                tension: 0.3,
                fill: false,
            };
        });

        createOrUpdateLineChart('temperature-chart-global', labels, tempDatasets, '温度 (°C)');
        createOrUpdateLineChart('light-chart-global', labels, lightDatasets, '光强');
    }

    async function loadSingleDeviceAnalysis() {
        const deviceSelector = document.getElementById('device-selector');
        const timeRangeSelector = document.getElementById('time-range-selector');

        if (!deviceSelector || !timeRangeSelector) {
            return;
        }

        const deviceSeq = deviceSelector.value;
        if (!deviceSeq) {
            renderSingleDeviceCharts([]);
            return;
        }

        const hours = parseInt(timeRangeSelector.value, 10);
        const now = Date.now() / 1000;
        const startTime = now - hours * 3600;
        const endTime = now;

        try {
            const result = await fetchAnalysisData(deviceSeq, startTime, endTime, 1000);
            renderSingleDeviceCharts(result.data || []);
        } catch (error) {
            console.error('加载单设备分析数据失败:', error);
            renderSingleDeviceCharts([]);
        }
    }

    async function loadGlobalAnalysis() {
        const timeRangeSelector = document.getElementById('global-time-range-selector');
        const recordLimitInput = document.getElementById('global-record-limit');

        if (!timeRangeSelector || !recordLimitInput) {
            return;
        }

        const hours = parseInt(timeRangeSelector.value, 10);
        const limit = parseInt(recordLimitInput.value, 10) || 500;
        const now = Date.now() / 1000;
        const startTime = now - hours * 3600;
        const endTime = now;

        try {
            const result = await fetchAnalysisData(null, startTime, endTime, limit);
            renderGlobalCharts(result.data || []);
        } catch (error) {
            console.error('加载全局分析数据失败:', error);
            renderGlobalCharts([]);
        }
    }

    async function populateDeviceSelector() {
        const deviceSelector = document.getElementById('device-selector');
        if (!deviceSelector) {
            return;
        }

        try {
            const devices = await getDeviceList();
            deviceSelector.innerHTML = '<option value="">-- 选择设备 --</option>';
            devices.forEach(seq => {
                const option = document.createElement('option');
                option.value = escapeHtml(seq);
                option.textContent = escapeHtml(seq);
                deviceSelector.appendChild(option);
            });
        } catch (error) {
            console.error('加载设备列表失败:', error);
        }
    }

    function initAnalysisView() {
        if (!document.getElementById('device-selector')) return;

        populateDeviceSelector();

        const deviceSelector = document.getElementById('device-selector');
        const timeRangeSelector = document.getElementById('time-range-selector');
        const globalTimeRangeSelector = document.getElementById('global-time-range-selector');
        const recordLimitInput = document.getElementById('global-record-limit');

        if (deviceSelector) {
            deviceSelector.addEventListener('change', () => {
                if (state.currentTab === 'single-device') {
                    loadSingleDeviceAnalysis();
                }
            });
        }

        if (timeRangeSelector) {
            timeRangeSelector.addEventListener('change', () => {
                if (state.currentTab === 'single-device') {
                    loadSingleDeviceAnalysis();
                }
            });
        }

        if (globalTimeRangeSelector) {
            globalTimeRangeSelector.addEventListener('change', () => {
                if (state.currentTab === 'all-devices') {
                    loadGlobalAnalysis();
                }
            });
        }

        if (recordLimitInput) {
            recordLimitInput.addEventListener('change', () => {
                if (state.currentTab === 'all-devices') {
                    loadGlobalAnalysis();
                }
            });
        }

        document.querySelectorAll('.analysis-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                document.querySelectorAll('.analysis-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.analysis-view').forEach(v => v.classList.remove('active'));

                this.classList.add('active');
                const tabName = this.dataset.tab;
                state.currentTab = tabName;

                const targetView = document.getElementById(`${tabName}-view`);
                if (targetView) {
                    targetView.classList.add('active');
                }

                if (tabName === 'single-device') {
                    loadSingleDeviceAnalysis();
                } else if (tabName === 'all-devices') {
                    loadGlobalAnalysis();
                }
            });
        });
    }

    window.initDataAnalysis = function() {
        initAnalysisView();
    };
});
