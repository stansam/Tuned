function refreshDashboard() {
    const refreshIcon = document.querySelector('.sync-button i');
    refreshIcon.style.animation = 'spin 1s linear infinite';
    
    setTimeout(() => {
        location.reload();
    }, 1000);
}