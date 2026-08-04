// app/static/js/main.js
// Các logic tiện ích dùng chung

/**
 * Cập nhật thông số hệ thống (CPU/RAM/Disk)
 */
async function updateSystemHealth() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) return;
        const data = await response.json();
        
        const cpuEl = document.getElementById('cpu-val');
        const ramEl = document.getElementById('ram-val');
        const diskEl = document.getElementById('disk-val');
        
        if (cpuEl) cpuEl.innerText = `${data.cpu_usage_percent}%`;
        if (ramEl) ramEl.innerText = `${data.ram_used_mb} MB`;
        if (diskEl) diskEl.innerText = `${data.disk_free_gb} GB Free`;
    } catch (err) {
        // Silent fail
    }
}

// Chạy định kỳ
if (document.getElementById('cpu-val')) {
    updateSystemHealth();
    setInterval(updateSystemHealth, 15000);
}
