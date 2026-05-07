// RFID卡管理模块
(function() {
    const PAGE_SIZE = 20;
    let currentPage = 0;
    let totalPages = 0;

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
                if (event.target === modal) close(false);
            });
            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
            modal.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
            document.body.appendChild(modal);
            modal.style.display = 'block';
        });
    }

    function createBalanceModal(uid, currentBalance) {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'confirmation-modal';
            modal.innerHTML = `
                <div class="confirmation-modal-content">
                    <h3>修改余额</h3>
                    <p>RFID卡 UID: ${escapeHtml(uid)}</p>
                    <p>当前余额: <strong>${currentBalance.toFixed(2)}</strong></p>
                    <hr style="margin: 10px 0;">
                    <label style="display: block; margin: 8px 0;">
                        <input type="radio" name="balance-mode" value="add" checked> 增加余额
                        <input type="radio" name="balance-mode" value="subtract" style="margin-left: 15px;"> 扣除余额
                        <input type="radio" name="balance-mode" value="set" style="margin-left: 15px;"> 直接设置
                    </label>
                    <input type="number" id="balance-amount-input" class="add-user-input" placeholder="金额" step="0.01" min="0" style="width: 100%; margin: 8px 0; padding: 8px;">
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-confirm" data-action="confirm">确认</button>
                        <button class="modal-btn modal-btn-cancel" data-action="cancel">取消</button>
                    </div>
                </div>
            `;
            let selectedMode = 'add';
            const close = (result) => {
                if (result) {
                    const amountInput = document.getElementById('balance-amount-input');
                    const amount = parseFloat(amountInput ? amountInput.value : '0');
                    const mode = selectedMode;
                    modal.remove();
                    resolve({ amount, mode });
                } else {
                    modal.remove();
                    resolve(null);
                }
            };
            modal.addEventListener('click', (event) => {
                if (event.target === modal) close(false);
            });
            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
            modal.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));

            modal.querySelectorAll('input[name="balance-mode"]').forEach(r => {
                r.addEventListener('change', function() {
                    selectedMode = this.value;
                    const input = document.getElementById('balance-amount-input');
                    if (this.value === 'subtract') {
                        input.placeholder = '扣除金额（正数）';
                    } else if (this.value === 'set') {
                        input.placeholder = '设置余额';
                    } else {
                        input.placeholder = '增加金额（正数）';
                    }
                });
            });
            document.body.appendChild(modal);
            modal.style.display = 'block';
        });
    }

    function createAddCardModal() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'confirmation-modal';
            modal.innerHTML = `
                <div class="confirmation-modal-content">
                    <h3>添加RFID卡</h3>
                    <input type="text" id="add-card-uid-input" class="add-user-input" placeholder="RFID卡UID（十六进制）" style="width: 100%; margin: 8px 0; padding: 8px;">
                    <input type="number" id="add-card-balance-input" class="add-user-input" placeholder="初始余额（可选，默认0）" step="0.01" min="0" style="width: 100%; margin: 8px 0; padding: 8px;">
                    <div class="modal-buttons">
                        <button class="modal-btn modal-btn-confirm" data-action="confirm">确认</button>
                        <button class="modal-btn modal-btn-cancel" data-action="cancel">取消</button>
                    </div>
                </div>
            `;
            const close = (result) => {
                if (result) {
                    const uidInput = document.getElementById('add-card-uid-input');
                    const balanceInput = document.getElementById('add-card-balance-input');
                    const uid = uidInput ? uidInput.value.trim() : '';
                    const balance = parseFloat(balanceInput ? balanceInput.value : '0') || 0;
                    modal.remove();
                    resolve({ uid, balance });
                } else {
                    modal.remove();
                    resolve(null);
                }
            };
            modal.addEventListener('click', (event) => {
                if (event.target === modal) close(false);
            });
            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => close(true));
            modal.querySelector('[data-action="cancel"]').addEventListener('click', () => close(false));
            document.body.appendChild(modal);
            modal.style.display = 'block';
        });
    }

    async function getRfidCards(start, num) {
        const response = await fetch('/dashboard/rfid_card/get_rfid_cards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ start, num })
        });
        if (response.status === 401) {
            window.location.href = '/admin';
            throw new Error('未登录');
        }
        const payload = await parseJsonSafe(response);
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '获取RFID卡列表失败');
        }
        return payload.cards || [];
    }

    async function addRfidCard(uid, balance) {
        const response = await fetch('/dashboard/rfid_card/add_rfid_card', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ uid, balance })
        });
        const payload = await parseJsonSafe(response);
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '添加失败');
        }
    }

    async function modifyBalance(uid, amount, mode) {
        const response = await fetch('/dashboard/rfid_card/modify_balance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ uid, amount, mode })
        });
        const payload = await parseJsonSafe(response);
        if (response.status === 404) {
            throw new Error(payload?.message || 'RFID卡不存在');
        }
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '操作失败');
        }
        return payload;
    }

    async function deleteRfidCard(uid) {
        const response = await fetch('/dashboard/rfid_card/delete_rfid_card', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ uid })
        });
        const payload = await parseJsonSafe(response);
        if (!response.ok || payload?.status !== 'success') {
            throw new Error(payload?.message || '删除失败');
        }
    }

    function formatTimestamp(ts) {
        const num = Number(ts);
        if (Number.isNaN(num)) return ts || 'N/A';
        const date = new Date(num * 1000);
        if (Number.isNaN(date.getTime())) return ts || 'N/A';
        return date.toLocaleString('zh-CN', {
            hour12: false, year: 'numeric', month: '2-digit',
            day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
        });
    }

    function formatBalance(balance) {
        const num = Number(balance);
        if (isNaN(num)) return '0.00';
        const cls = num > 0 ? 'balance-positive' : (num < 0 ? 'balance-negative' : 'balance-zero');
        return `<span class="${cls}">${num.toFixed(2)}</span>`;
    }

    function renderTable(cards) {
        const tbody = document.querySelector('#rfid-card-table tbody');
        if (!tbody) return;
        if (!cards.length) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">暂无RFID卡</td></tr>';
            return;
        }
        tbody.innerHTML = cards.map(c => {
            const safeUid = escapeHtml(c.uid);
            return `
                <tr>
                    <td>${safeUid}</td>
                    <td>${formatBalance(c.balance)}</td>
                    <td>${escapeHtml(formatTimestamp(c.created_at))}</td>
                    <td>
                        <button class="action-btn btn-modify-balance" data-uid="${safeUid}" data-balance="${c.balance}">修改余额</button>
                        <button class="action-btn btn-delete-card" data-uid="${safeUid}">删除</button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function updatePagination() {
        const info = document.getElementById('rfid-card-page-info');
        const prevBtn = document.getElementById('rfid-card-prev-btn');
        const nextBtn = document.getElementById('rfid-card-next-btn');
        if (info) info.textContent = `第 ${currentPage + 1} 页 / 共 ${totalPages} 页`;
        if (prevBtn) prevBtn.disabled = currentPage <= 0;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages - 1;
    }

    function loadPage(page) {
        currentPage = page;
        getRfidCards(0, 1000).then(cards => {
            totalPages = Math.max(1, Math.ceil(cards.length / PAGE_SIZE));
            currentPage = Math.min(currentPage, totalPages - 1);
            const startIdx = currentPage * PAGE_SIZE;
            renderTable(cards.slice(startIdx, startIdx + PAGE_SIZE));
            updatePagination();
        }).catch(err => {
            const tbody = document.querySelector('#rfid-card-table tbody');
            if (tbody) tbody.innerHTML = `<tr><td colspan="4">加载失败: ${escapeHtml(err.message)}</td></tr>`;
        });
    }

    function bindEvents() {
        const addBtn = document.getElementById('rfid-card-add-btn');
        const refreshBtn = document.getElementById('rfid-card-refresh-btn');
        const prevBtn = document.getElementById('rfid-card-prev-btn');
        const nextBtn = document.getElementById('rfid-card-next-btn');

        if (addBtn) {
            addBtn.addEventListener('click', async () => {
                const result = await createAddCardModal();
                if (!result || !result.uid) return;
                try {
                    await addRfidCard(result.uid, result.balance);
                    showMessage('RFID卡添加成功');
                    loadPage(0);
                } catch (err) {
                    showMessage(`添加失败: ${err.message}`);
                }
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => loadPage(currentPage));
        }

        if (prevBtn) prevBtn.addEventListener('click', () => loadPage(currentPage - 1));
        if (nextBtn) nextBtn.addEventListener('click', () => loadPage(currentPage + 1));

        const tbody = document.querySelector('#rfid-card-table tbody');
        if (tbody) {
            tbody.addEventListener('click', async (event) => {
                const target = event.target;
                if (!(target instanceof HTMLElement)) return;
                const uid = target.dataset.uid;
                if (!uid) return;

                if (target.classList.contains('btn-modify-balance')) {
                    const currentBalance = parseFloat(target.dataset.balance) || 0;
                    const result = await createBalanceModal(uid, currentBalance);
                    if (!result) return;
                    let { amount, mode } = result;

                    if (mode === 'subtract') {
                        amount = -Math.abs(amount);
                        mode = 'add';
                    }

                    if (isNaN(amount) || amount === 0) {
                        showMessage('请输入有效金额');
                        return;
                    }
                    try {
                        const resp = await modifyBalance(uid, amount, mode);
                        showMessage(resp.message || '余额修改成功');
                        loadPage(currentPage);
                    } catch (err) {
                        showMessage(`操作失败: ${err.message}`);
                    }
                    return;
                }

                if (target.classList.contains('btn-delete-card')) {
                    const confirmed = await createConfirmModal(`确定要删除RFID卡 ${uid} 吗？此操作不可恢复。`);
                    if (!confirmed) return;
                    try {
                        await deleteRfidCard(uid);
                        showMessage('RFID卡删除成功');
                        loadPage(currentPage);
                    } catch (err) {
                        showMessage(`删除失败: ${err.message}`);
                    }
                }
            });
        }
    }

    function init() {
        bindEvents();
        loadPage(0);
    }

    window.initRfidCard = init;
})();
