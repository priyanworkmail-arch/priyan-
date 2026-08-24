// Auto-refresh availability stats every 30 seconds on the home page
if (document.getElementById('stat-beds')) {
    setInterval(async () => {
        try {
            const resp = await fetch('/api/availability');
            const data = await resp.json();
            const totalBeds = data.reduce((s, h) => s + h.available_beds, 0);
            const totalDoctors = data.reduce((s, h) => s + h.doctors_available, 0);
            document.getElementById('stat-beds').textContent = totalBeds;
            document.getElementById('stat-doctors').textContent = totalDoctors;
        } catch (e) { /* silent */ }
    }, 30000);
}
