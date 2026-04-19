// 用户管理页面 JavaScript 逻辑

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

function createEditModal(username) {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'confirmation-modal';
        modal.innerHTML = `
            <div class="confirmation-modal-content">
                <h3>修改用户密码</h3>
                <p>用户名: ${escapeHtml(username)}</p>
                <input type="password" id="edit-password-input" class="add-user-input" placeholder="新密码" style="width: 100%; margin: 10px 0; padding: 8px;">
                <div class="modal-buttons">
                    <button class="modal-btn modal-btn-confirm" data-action="confirm">确认</button>
                    <button class="modal-btn modal-btn-cancel" data-action="cancel">取消</button>
                </div>
            </div>
        `;

        const close = (result) => {
            if (result) {
                const passwordInput = document.getElementById('edit-password-input');
                const value = passwordInput ? passwordInput.value : null;
                modal.remove();
                resolve(value);
            } else {
                modal.remove();
                resolve(null);
            }
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

async function getAllUsers() {
    const response = await fetch('/dashboard/get_all_users', {
        method: 'GET',
        credentials: 'include'
    });

    const payload = await parseJsonSafe(response);
    if (response.status === 401) {
        window.location.href = '/admin';
        throw new Error('未登录');
    }
    if (response.status === 403) {
        throw new Error('权限不足');
    }
    if (!response.ok || payload?.status !== 'success') {
        throw new Error(payload?.message || '获取用户列表失败');
    }

    return payload.users || [];
}

async function addUser(username, password) {
    const response = await fetch('/dashboard/add_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
    });

    const payload = await parseJsonSafe(response);
    if (response.status === 401) {
        window.location.href = '/admin';
        throw new Error('未登录');
    }
    if (response.status === 403) {
        throw new Error('权限不足');
    }
    if (!response.ok || payload?.status !== 'success') {
        throw new Error(payload?.message || '添加用户失败');
    }
}

async function updateUser(username, newPassword) {
    const response = await fetch('/dashboard/update_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, new_password: newPassword }),
    });

    const payload = await parseJsonSafe(response);
    if (response.status === 401) {
        window.location.href = '/admin';
        throw new Error('未登录');
    }
    if (response.status === 403) {
        throw new Error('权限不足');
    }
    if (!response.ok || payload?.status !== 'success') {
        throw new Error(payload?.message || '更新用户失败');
    }
}

async function deleteUser(username) {
    const response = await fetch('/dashboard/delete_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username }),
    });

    const payload = await parseJsonSafe(response);
    if (response.status === 401) {
        window.location.href = '/admin';
        throw new Error('未登录');
    }
    if (response.status === 403) {
        throw new Error('权限不足');
    }
    if (!response.ok || payload?.status !== 'success') {
        throw new Error(payload?.message || '删除用户失败');
    }
}

function formatTimestamp(timestamp) {
    const num = Number(timestamp);
    if (Number.isNaN(num)) {
        return timestamp || 'N/A';
    }

    const date = new Date(num * 1000);
    if (Number.isNaN(date.getTime())) {
        return timestamp || 'N/A';
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

function renderUserRows(users) {
    const tbody = document.querySelector('#user-list-table tbody');
    if (!tbody) {
        return;
    }

    if (!users.length) {
        tbody.innerHTML = '<tr><td colspan="4">暂无用户</td></tr>';
        return;
    }

    tbody.innerHTML = users
        .map((user) => {
            const safeUsername = escapeHtml(user.username);
            const isRoot = user.username === 'root';
            return `
                <tr>
                    <td>${user.id}</td>
                    <td>${safeUsername}${isRoot ? ' <span style="color: #e74c3c; font-size: 12px;">(root)</span>' : ''}</td>
                    <td>${escapeHtml(formatTimestamp(user.timestamp))}</td>
                    <td>
                        ${isRoot ? '<span style="color: #999;">不可操作</span>' : `
                            <button class="edit-user-btn" data-username="${safeUsername}">修改密码</button>
                            <button class="delete-user-btn" data-username="${safeUsername}">删除</button>
                        `}
                    </td>
                </tr>
            `;
        })
        .join('');
}

function bindEvents() {
    const addUserBtn = document.getElementById('add-user-btn');
    const addUserForm = document.getElementById('add-user-form');
    const submitBtn = document.getElementById('add-user-submit-btn');
    const cancelBtn = document.getElementById('cancel-add-user-btn');
    const usernameInput = document.getElementById('new-username-input');
    const passwordInput = document.getElementById('new-password-input');

    if (!addUserBtn || !addUserForm) return;

    const toggleAddForm = () => {
        const visible = addUserForm.style.display === 'block';
        addUserForm.style.display = visible ? 'none' : 'block';
        addUserBtn.textContent = visible ? '添加用户' : '取消添加';
        if (visible) {
            usernameInput.value = '';
            passwordInput.value = '';
        }
    };

    addUserBtn.addEventListener('click', toggleAddForm);

    cancelBtn.addEventListener('click', () => {
        addUserForm.style.display = 'none';
        addUserBtn.textContent = '添加用户';
        usernameInput.value = '';
        passwordInput.value = '';
    });

    submitBtn.addEventListener('click', async () => {
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username) {
            showMessage('请输入用户名');
            return;
        }

        if (!password) {
            showMessage('请输入密码');
            return;
        }

        try {
            submitBtn.disabled = true;
            await addUser(username, password);
            showMessage('用户添加成功');
            addUserForm.style.display = 'none';
            addUserBtn.textContent = '添加用户';
            usernameInput.value = '';
            passwordInput.value = '';
            await loadUserList();
        } catch (error) {
            showMessage(`添加失败: ${error.message}`);
        } finally {
            submitBtn.disabled = false;
        }
    });

    const tbody = document.querySelector('#user-list-table tbody');
    tbody.addEventListener('click', async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) {
            return;
        }

        const username = target.dataset.username;
        if (!username) {
            return;
        }

        if (target.classList.contains('edit-user-btn')) {
            const newPassword = await createEditModal(username);
            if (!newPassword) {
                return;
            }
            if (!newPassword.trim()) {
                showMessage('请输入新密码');
                return;
            }

            try {
                await updateUser(username, newPassword);
                showMessage('密码修改成功');
            } catch (error) {
                showMessage(`修改失败: ${error.message}`);
            }
            return;
        }

        if (target.classList.contains('delete-user-btn')) {
            const confirmed = await createConfirmModal(`确定要删除用户 ${username} 吗？此操作不可恢复。`);
            if (!confirmed) {
                return;
            }

            try {
                await deleteUser(username);
                showMessage('用户删除成功');
                await loadUserList();
            } catch (error) {
                showMessage(`删除失败: ${error.message}`);
            }
        }
    });
}

async function loadUserList() {
    try {
        const users = await getAllUsers();
        renderUserRows(users);
    } catch (error) {
        const tbody = document.querySelector('#user-list-table tbody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="4">加载失败: ${escapeHtml(error.message)}</td></tr>`;
        }
    }
}

// Called by the inline script in dashboard.html after DOM is ready
window.initUserManagement = function() {
    bindEvents();
    loadUserList();
};
