// 刷卡记录模块
(function() {
    const PAGE_SIZE = 20;
    let currentPage = 0;
    let totalPages = 0;
    let currentDevice = '';
    let currentStartTime = 0;
    let currentEndTime = 0;

    // 初始化
    function init() {
        loadDeviceList();
        setupEventListeners();
        // 默认加载最近7天的数据
        setQuickRange(7);
        queryCardSwipes();
    }

    // 加载设备列表
    function loadDeviceList() {
        fetch('/api/get_device_list', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include'
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.status === 'success') {
                const selector = document.getElementById('card-swipe-device-selector');
                data.devices.forEach(seq => {
                    const opt = document.createElement('option');
                    opt.value = seq;
                    opt.textContent = seq;
                    selector.appendChild(opt);
                });
            }
        });
    }

    // 解析时间戳为 Unix 时间戳（秒）
    function parseTimestamp(ts) {
        const num = parseFloat(ts);
        if (isNaN(num)) {
            // 旧格式 "2026-04-26 10:00:00" 转换为 Unix 时间戳
            return new Date(ts).getTime() / 1000;
        }
        return num;
    }

    // 设置快捷时间范围
    function setQuickRange(days, btnElement) {
        // 移除所有快捷按钮的 active 状态
        document.querySelectorAll('.card-swipe-filters .quick-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        // 添加当前按钮的 active 状态
        if (btnElement) {
            btnElement.classList.add('active');
        }

        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - days);

        document.getElementById('card-swipe-end-date').value = formatDate(end);
        document.getElementById('card-swipe-start-date').value = formatDate(start);

        currentEndTime = Math.floor(end.getTime() / 1000);
        currentStartTime = Math.floor(start.getTime() / 1000);

        // 自动触发查询
        queryCardSwipes();
    }

    // 格式化日期为 YYYY-MM-DD
    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    // 绑定事件
    function setupEventListeners() {
        document.getElementById('card-swipe-quick-1day').addEventListener('click', function() {
            setQuickRange(1, this);
        });
        document.getElementById('card-swipe-quick-7days').addEventListener('click', function() {
            setQuickRange(7, this);
        });
        document.getElementById('card-swipe-quick-30days').addEventListener('click', function() {
            setQuickRange(30, this);
        });
        document.getElementById('card-swipe-query-btn').addEventListener('click', () => {
            // 移除快捷按钮的 active 状态（手动查询）
            document.querySelectorAll('.card-swipe-filters .quick-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            queryCardSwipes();
        });
        document.getElementById('card-swipe-prev-btn').addEventListener('click', () => loadPage(currentPage - 1));
        document.getElementById('card-swipe-next-btn').addEventListener('click', () => loadPage(currentPage + 1));

        // 设备选择变化时重置页码
        document.getElementById('card-swipe-device-selector').addEventListener('change', () => {
            currentPage = 0;
            queryCardSwipes();
        });
    }

    // 查询刷卡记录
    function queryCardSwipes() {
        currentDevice = document.getElementById('card-swipe-device-selector').value || null;

        const startDateVal = document.getElementById('card-swipe-start-date').value;
        const endDateVal = document.getElementById('card-swipe-end-date').value;

        if (startDateVal) {
            currentStartTime = Math.floor(new Date(startDateVal + 'T00:00:00+08:00').getTime() / 1000);
        } else {
            currentStartTime = 0;
        }
        if (endDateVal) {
            currentEndTime = Math.floor(new Date(endDateVal + 'T23:59:59+08:00').getTime() / 1000);
        } else {
            currentEndTime = 0;
        }

        loadPage(0);
    }

    // 加载指定页
    function loadPage(page) {
        currentPage = page;

        const params = {
            start: 0,
            num: 1000
        };

        if (currentDevice) {
            params.device_seq = currentDevice;
        }

        fetch('/api/fetch_card_swipe', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify(params)
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.status === 'success') {
                // 前端过滤时间范围
                let filtered = data.swipes;
                if (currentStartTime > 0) {
                    filtered = filtered.filter(s => parseTimestamp(s.timestamp) >= currentStartTime);
                }
                if (currentEndTime > 0) {
                    filtered = filtered.filter(s => parseTimestamp(s.timestamp) <= currentEndTime);
                }
                if (currentDevice) {
                    filtered = filtered.filter(s => s.device_seq === currentDevice);
                }

                totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
                currentPage = Math.min(currentPage, totalPages - 1);

                const startIdx = currentPage * PAGE_SIZE;
                const pageData = filtered.slice(startIdx, startIdx + PAGE_SIZE);

                renderTable(pageData);
                updatePagination();
            }
        });
    }

    // 渲染表格
    function renderTable(swipes) {
        const tbody = document.querySelector('#card-swipe-table tbody');
        tbody.innerHTML = '';

        if (swipes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">暂无记录</td></tr>';
            return;
        }

        swipes.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.device_seq}</td>
                <td>${s.rfid_serial}</td>
                <td>${formatTimestamp(s.timestamp)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // 格式化时间戳为北京时间 YYYY-MM-DD HH:mm:ss
    function formatTimestamp(ts) {
        const date = new Date(parseFloat(ts) * 1000);
        const beijing = new Date(date.getTime() + 8 * 60 * 60 * 1000);
        return beijing.toISOString().replace('T', ' ').split('.')[0];
    }

    // 更新分页信息
    function updatePagination() {
        document.getElementById('card-swipe-page-info').textContent =
            `第 ${currentPage + 1} 页 / 共 ${totalPages} 页`;

        document.getElementById('card-swipe-prev-btn').disabled = currentPage <= 0;
        document.getElementById('card-swipe-next-btn').disabled = currentPage >= totalPages - 1;
    }

    // 对外暴露初始化函数
    window.initCardSwipe = init;
})();
