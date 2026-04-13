// auth.js - Session-based auth helpers

async function checkAuth() {
    try {
        const resp = await fetch('/dashboard/check', { credentials: 'include' });
        if (resp.ok) {
            const data = await resp.json();
            return { authenticated: true, username: data.username };
        }
        return { authenticated: false };
    } catch (_) {
        return { authenticated: false };
    }
}

async function login(username, password) {
    const resp = await fetch('/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.message || 'Login failed');
    return data;
}

async function logout() {
    await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
}
