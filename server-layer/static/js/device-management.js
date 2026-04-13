// 设备管理页面 JavaScript 逻辑

document.addEventListener('DOMContentLoaded', () => {
    const ITEMS_PER_PAGE = 10;

    const state = {
        currentDeviceSeq: null,
        currentPage: 1,
        hasNextPage: false,
        selectedRows: new Set(),
        selectionMode: false,
        ready: false,
    };

    const deviceManagementSection = document.getElementById('delete-section');
    if (!deviceManagementSection) {
        console.error('未找到设备管理容器 #delete-section');
        return;
    }

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
        const response = await fetch('/api/get_device_list', { method: 'GET' });
        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }
        const payload = await parseJsonSafe(response);

        if (!response.ok) {
            throw new Error(payload?.message || '获取设备列表失败');
        }

        return Array.isArray(payload) ? payload : [];
    }

    async function addDevice(deviceSeq) {
        const response = await fetch('/api/add_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_seq: deviceSeq,
                timestamp: String(Date.now() / 1000),
            }),
        });

        const payload = await parseJsonSafe(response);
        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '添加设备失败');
        }
    }

    async function removeDevice(deviceSeq) {
        const response = await fetch('/api/remove_device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_seq: deviceSeq }),
        });

        const payload = await parseJsonSafe(response);
        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '删除设备失败');
        }
    }

    async function fetchSensorDataPage(deviceSeq, page) {
        const startIndex = (page - 1) * ITEMS_PER_PAGE;
        const response = await fetch('/api/fetch_sensor_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start: startIndex,
                num: ITEMS_PER_PAGE,
                device_seq: deviceSeq,
            }),
        });

        const payload = await parseJsonSafe(response);

        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }

        if (response.ok && Array.isArray(payload)) {
            return payload;
        }

        // 当前后端在"无数据"时返回 400 + {}，这里按空数据处理，避免误报错误。
        if (response.status === 400 && payload && !Array.isArray(payload)) {
            return [];
        }

        throw new Error(payload?.message || '获取传感器数据失败');
    }

    async function removeSensorData(deviceSeq, id) {
        const response = await fetch('/api/remove_sensor_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id, device_seq: deviceSeq }),
        });

        const payload = await parseJsonSafe(response);
        if (response.status === 401) {
            showLoginModal();
            throw new Error('Login required');
        }
        if (!response.ok || payload?.rcv_status !== 'success') {
            throw new Error(payload?.message || '删除传感器数据失败');
        }
    }

    async function removeSensorDataBatch(deviceSeq, ids) {
        const requests = ids.map((id) =>
            fetch('/api/remove_sensor_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, device_seq: deviceSeq }),
            }).then(async (response) => {
                const payload = await parseJsonSafe(response);
                return response.ok && payload?.rcv_status === 'success';
            })
        );

        const results = await Promise.all(requests);
        const success = results.filter(Boolean).length;
        const fail = results.length - success;
        return { success, fail };
    }

    function showMessage(message) {
        alert(message);
    }

    function createConfirmModal(message) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'confirmation-modal';
            modal.innerHTML = `
                <div class="confirmation-modal-content">
                    <h3>确认操作</h3>
                    <p>${escapeHtml(message)}</p>
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-confirm" data-action="confirm">确认</button>
                        <button class="modal-btn modal-btn-cancel" data-action="cancel">取消</button>
                    </div>
                </div>
            `;

            const close = (result) => {
                modal.remove();
                resolve(result);
            };

            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    close(false);
                }
            });

            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
            modal.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));

            document.body.appendChild(modal);
            modal.style.display = 'block';
        });
    }

    function formatTimestamp(rawTimestamp) {
        const num = Number(rawTimestamp);
        if (Number.isNaN(num)) {
            return rawTimestamp ?? 'N/A';
        }

        const date = new Date(num * 1000);
        if (Number.isNaN(date.getTime())) {
            return rawTimestamp ?? 'N/A';
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

    function renderDeviceListShell() {
        deviceManagementSection.innerHTML = `
            <div class="device-management-container">
                <div class="device-list-container">
                    <div class="device-list-header">
                        <h2 class="device-list-title">设备管理</h2>
                        <button class="add-device-btn" id="add-device-btn">添加设备</button>
                    </div>
                    <form class="add-device-form" id="add-device-form">
                        <h3>添加新设备</h3>
                        <input type="text" id="device-seq-input" class="add-device-input" placeholder="请输入设备序列号">
                        <button type="button" class="add-device-submit-btn" id="add-device-submit-btn">提交</button>
                        <button type="button" class="cancel-add-device-btn" id="cancel-add-device-btn">取消</button>
                    </form>
                    <table class="device-table" id="device-list-table">
                        <thead>
                            <tr>
                                <th>设备序列号</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        `;

        const addDeviceBtn = document.getElementById('add-device-btn');
        const addDeviceForm = document.getElementById('add-device-form');
        const submitBtn = document.getElementById('add-device-submit-btn');
        const cancelBtn = document.getElementById('cancel-add-device-btn');
        const input = document.getElementById('device-seq-input');

        const toggleAddForm = () => {
            const visible = addDeviceForm.style.display === 'block';
            addDeviceForm.style.display = visible ? 'none' : 'block';
            addDeviceBtn.textContent = visible ? '添加设备' : '取消添加';
            if (visible) {
                input.value = '';
            }
        };

        addDeviceBtn.addEventListener('click', toggleAddForm);
        cancelBtn.addEventListener('click', () => {
            addDeviceForm.style.display = 'none';
            addDeviceBtn.textContent = '添加设备';
            input.value = '';
        });

        submitBtn.addEventListener('click', async () => {
            const deviceSeq = input.value.trim();
            if (!deviceSeq) {
                showMessage('请输入设备序列号');
                return;
            }

            try {
                submitBtn.disabled = true;
                await addDevice(deviceSeq);
                showMessage('设备添加成功');
                await loadDeviceListView();
            } catch (error) {
                showMessage(`添加失败: ${error.message}`);
            } finally {
                submitBtn.disabled = false;
            }
        });

        const tbody = document.querySelector('#device-list-table tbody');
        tbody.addEventListener('click', async (event) => {
            const target = event.target;
            if (!(target instanceof HTMLElement)) {
                return;
            }

            const deviceSeq = target.dataset.device;
            if (!deviceSeq) {
                return;
            }

            if (target.classList.contains('view-data-btn')) {
                await showSensorDataView(deviceSeq);
                return;
            }

            if (target.classList.contains('delete-device-btn')) {
                const confirmed = await createConfirmModal(
                    `确定要删除设备 ${deviceSeq} 吗？此操作将删除设备及其所有传感器数据。`
                );
                if (!confirmed) {
                    return;
                }

                try {
                    await removeDevice(deviceSeq);
                    showMessage('设备删除成功');
                    await loadDeviceListView();
                } catch (error) {
                    showMessage(`删除失败: ${error.message}`);
                }
            }
        });
    }

    function renderDeviceRows(devices) {
        const tbody = document.querySelector('#device-list-table tbody');
        if (!tbody) {
            return;
        }

        if (!devices.length) {
            tbody.innerHTML = '<tr><td colspan="2">暂无设备</td></tr>';
            return;
        }

        tbody.innerHTML = devices
            .map((deviceSeq) => {
                const safeDeviceSeq = escapeHtml(deviceSeq);
                return `
                    <tr>
                        <td>${safeDeviceSeq}</td>
                        <td>
                            <button class="view-data-btn" data-device="${safeDeviceSeq}">查看数据</button>
                            <button class="delete-device-btn" data-device="${safeDeviceSeq}">删除设备</button>
                        </td>
                    </tr>
                `;
            })
            .join('');
    }

    async function loadDeviceListView() {
        if (!state.ready) return;

        state.currentDeviceSeq = null;
        state.currentPage = 1;
        state.hasNextPage = false;
        state.selectionMode = false;
        state.selectedRows.clear();

        renderDeviceListShell();

        try {
            const devices = await getDeviceList();
            renderDeviceRows(devices);
        } catch (error) {
            const tbody = document.querySelector('#device-list-table tbody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="2">加载失败: ${escapeHtml(error.message)}</td></tr>`;
            }
        }
    }

    function renderSensorDataShell(deviceSeq) {
        deviceManagementSection.innerHTML = `
            <div class="sensor-data-container">
                <div class="sensor-data-header">
                    <h2 class="sensor-data-title">设备 ${escapeHtml(deviceSeq)} 的传感器数据</h2>
                    <button class="back-to-devices-btn" id="back-to-devices">返回设备列表</button>
                </div>

                <div class="bulk-actions">
                    <button class="toggle-selection-btn" id="toggle-selection">选择数据</button>
                    <button class="delete-selected-btn" id="delete-selected" disabled>删除选中</button>
                    <span class="selected-count" id="selected-count">未选择任何数据</span>
                </div>

                <table class="sensor-data-table" id="sensor-data-table">
                    <thead>
                        <tr>
                            <th><input type="checkbox" class="select-all-checkbox" id="select-all-checkbox" style="display:none;"></th>
                            <th>ID</th>
                            <th>温度</th>
                            <th>光强</th>
                            <th>霍尔</th>
                            <th>时间戳</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="sensor-data-tbody"></tbody>
                </table>

                <div class="pagination-controls" id="pagination-controls"></div>
            </div>
        `;

        document.getElementById('back-to-devices').addEventListener('click', async () => {
            await loadDeviceListView();
        });

        bindBulkActionEvents();
    }

    function renderSensorRows(rows) {
        const tbody = document.getElementById('sensor-data-tbody');
        if (!tbody) {
            return;
        }

        if (!rows.length) {
            tbody.innerHTML = '<tr><td colspan="7">暂无传感器数据</td></tr>';
            return;
        }

        tbody.innerHTML = rows
            .map((item) => {
                const id = Number(item.id);
                const checked = state.selectedRows.has(id) ? 'checked' : '';
                const checkboxDisplay = state.selectionMode ? '' : 'style="display:none;"';
                return `
                    <tr data-id="${id}">
                        <td><input type="checkbox" class="select-checkbox" data-id="${id}" ${checked} ${checkboxDisplay}></td>
                        <td>${id}</td>
                        <td>${item.temperature ?? 'N/A'}</td>
                        <td>${item.light ?? 'N/A'}</td>
                        <td>${item.hall ?? 'N/A'}</td>
                        <td>${escapeHtml(formatTimestamp(item.timestamp))}</td>
                        <td><button class="delete-device-btn delete-sensor-data-btn" data-id="${id}">删除</button></td>
                    </tr>
                `;
            })
            .join('');

        tbody.querySelectorAll('.select-checkbox').forEach((checkbox) => {
            checkbox.addEventListener('change', () => {
                const id = Number(checkbox.dataset.id);
                if (checkbox.checked) {
                    state.selectedRows.add(id);
                } else {
                    state.selectedRows.delete(id);
                }
                syncSelectAllState();
                updateSelectedCount();
            });
        });

        tbody.querySelectorAll('.delete-sensor-data-btn').forEach((button) => {
            button.addEventListener('click', async () => {
                const id = Number(button.dataset.id);
                const confirmed = await createConfirmModal('确定要删除这条传感器数据吗？');
                if (!confirmed) {
                    return;
                }

                try {
                    await removeSensorData(state.currentDeviceSeq, id);
                    showMessage('传感器数据删除成功');
                    await loadSensorData(state.currentPage);
                } catch (error) {
                    showMessage(`删除失败: ${error.message}`);
                }
            });
        });

        syncSelectAllState();
        updateSelectedCount();
    }

    function updateSelectedCount() {
        const countEl = document.getElementById('selected-count');
        const deleteBtn = document.getElementById('delete-selected');

        if (countEl) {
            countEl.textContent =
                state.selectedRows.size > 0 ? `已选择 ${state.selectedRows.size} 条数据` : '未选择任何数据';
        }

        if (deleteBtn) {
            deleteBtn.disabled = state.selectedRows.size === 0;
        }
    }

    function syncSelectAllState() {
        const checkboxes = Array.from(document.querySelectorAll('.select-checkbox'));
        const selectAllCheckbox = document.getElementById('select-all-checkbox');

        if (!selectAllCheckbox) {
            return;
        }

        if (!checkboxes.length) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
            return;
        }

        const checkedCount = checkboxes.filter((checkbox) => checkbox.checked).length;
        selectAllCheckbox.checked = checkedCount === checkboxes.length;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }

    function updatePaginationControls() {
        const container = document.getElementById('pagination-controls');
        if (!container) {
            return;
        }

        container.innerHTML = '';

        const prevBtn = document.createElement('button');
        prevBtn.className = 'pagination-btn';
        prevBtn.textContent = '上一页';
        prevBtn.disabled = state.currentPage <= 1;
        prevBtn.addEventListener('click', async () => {
            if (state.currentPage <= 1) {
                return;
            }
            await loadSensorData(state.currentPage - 1);
        });

        const pageInfo = document.createElement('span');
        pageInfo.className = 'page-number';
        pageInfo.textContent = `第 ${state.currentPage} 页`;

        const nextBtn = document.createElement('button');
        nextBtn.className = 'pagination-btn';
        nextBtn.textContent = '下一页';
        nextBtn.disabled = !state.hasNextPage;
        nextBtn.addEventListener('click', async () => {
            if (!state.hasNextPage) {
                return;
            }
            await loadSensorData(state.currentPage + 1);
        });

        const pageInput = document.createElement('input');
        pageInput.type = 'number';
        pageInput.min = '1';
        pageInput.placeholder = '页码';
        pageInput.style.width = '60px';
        pageInput.style.padding = '5px';
        pageInput.style.margin = '0 5px';

        const goBtn = document.createElement('button');
        goBtn.className = 'pagination-btn';
        goBtn.textContent = '跳转';
        goBtn.addEventListener('click', async () => {
            const targetPage = Number(pageInput.value);
            if (!Number.isInteger(targetPage) || targetPage < 1) {
                showMessage('请输入大于 0 的整数页码');
                return;
            }
            await loadSensorData(targetPage);
        });

        container.appendChild(prevBtn);
        container.appendChild(pageInfo);
        container.appendChild(pageInput);
        container.appendChild(goBtn);
        container.appendChild(nextBtn);
    }

    function bindBulkActionEvents() {
        const toggleBtn = document.getElementById('toggle-selection');
        const deleteSelectedBtn = document.getElementById('delete-selected');
        const selectAllCheckbox = document.getElementById('select-all-checkbox');

        if (!toggleBtn || !deleteSelectedBtn || !selectAllCheckbox) {
            return;
        }

        toggleBtn.addEventListener('click', () => {
            state.selectionMode = !state.selectionMode;
            toggleBtn.textContent = state.selectionMode ? '取消选择' : '选择数据';

            if (!state.selectionMode) {
                state.selectedRows.clear();
            }

            const display = state.selectionMode ? '' : 'none';
            selectAllCheckbox.style.display = display;
            document.querySelectorAll('.select-checkbox').forEach((checkbox) => {
                checkbox.style.display = display;
                if (!state.selectionMode) {
                    checkbox.checked = false;
                }
            });

            syncSelectAllState();
            updateSelectedCount();
        });

        selectAllCheckbox.addEventListener('change', () => {
            const rowCheckboxes = Array.from(document.querySelectorAll('.select-checkbox'));
            if (!rowCheckboxes.length) {
                return;
            }

            if (selectAllCheckbox.checked) {
                rowCheckboxes.forEach((checkbox) => {
                    checkbox.checked = true;
                    state.selectedRows.add(Number(checkbox.dataset.id));
                });
            } else {
                rowCheckboxes.forEach((checkbox) => {
                    checkbox.checked = false;
                    state.selectedRows.delete(Number(checkbox.dataset.id));
                });
            }

            syncSelectAllState();
            updateSelectedCount();
        });

        deleteSelectedBtn.addEventListener('click', async () => {
            if (state.selectedRows.size === 0) {
                return;
            }

            const ids = Array.from(state.selectedRows);
            const confirmed = await createConfirmModal(`确定要删除选中的 ${ids.length} 条传感器数据吗？`);
            if (!confirmed) {
                return;
            }

            try {
                const { success, fail } = await removeSensorDataBatch(state.currentDeviceSeq, ids);
                if (fail > 0) {
                    showMessage(`批量删除完成：成功 ${success} 条，失败 ${fail} 条`);
                } else {
                    showMessage(`批量删除成功：共 ${success} 条`);
                }
                await loadSensorData(state.currentPage);
            } catch (error) {
                showMessage(`删除失败: ${error.message}`);
            }
        });
    }

    async function loadSensorData(page) {
        if (!state.ready) return;

        const targetPage = Math.max(1, page);

        try {
            const rows = await fetchSensorDataPage(state.currentDeviceSeq, targetPage);

            // 删除后可能出现当前页空白，自动回退到上一页。
            if (targetPage > 1 && rows.length === 0) {
                await loadSensorData(targetPage - 1);
                return;
            }

            state.currentPage = targetPage;
            state.hasNextPage = rows.length === ITEMS_PER_PAGE;

            // 切页时仅保留当前页有效的选中项。
            const rowIdSet = new Set(rows.map((item) => Number(item.id)));
            state.selectedRows.forEach((id) => {
                if (!rowIdSet.has(id)) {
                    state.selectedRows.delete(id);
                }
            });

            renderSensorRows(rows);
            updatePaginationControls();
        } catch (error) {
            const tbody = document.getElementById('sensor-data-tbody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="7">加载失败: ${escapeHtml(error.message)}</td></tr>`;
            }
            state.hasNextPage = false;
            updatePaginationControls();
        }
    }

    async function showSensorDataView(deviceSeq) {
        state.currentDeviceSeq = deviceSeq;
        state.currentPage = 1;
        state.hasNextPage = false;
        state.selectionMode = false;
        state.selectedRows.clear();

        renderSensorDataShell(deviceSeq);
        await loadSensorData(1);
    }

    // Called by the inline script in dashboard.html after auth is confirmed
    window.initDeviceManagement = function() {
        state.ready = true;
        loadDeviceListView();
    };
});
