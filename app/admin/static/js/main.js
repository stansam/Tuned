class AdminInterface {
    constructor() {
        this.elements = {};
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.cacheElements();
        this.initSidebar();
        this.initMobileHandlers();
        
        this.isInitialized = true;
    }
    
    cacheElements() {
        this.elements = {
            sidebarToggle: document.getElementById('sidebar-toggle'),
            adminSidebar: document.getElementById('admin-sidebar'),
            mainContent: document.querySelector('.main-content'),
            body: document.body
        };
    }
    
    initSidebar() {
        const { sidebarToggle, adminSidebar, mainContent } = this.elements;
        
        if (!sidebarToggle || !adminSidebar || !mainContent) {
            if(!sidebarToggle){
                console.warn('Sidebar toggle not found');
            } else if(!adminSidebar) {
                console.warn('admin sidebar not found');
            } else {
                console.warn('Main content not found');
            }
            console.warn('Sidebar elements not found');
            return;
        }
        
        sidebarToggle.addEventListener('click', () => {
            adminSidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }
    
    initMobileHandlers() {
        if (window.innerWidth >= 992) return;
        
        const { adminSidebar, sidebarToggle, body } = this.elements;
        
        if (!adminSidebar || !sidebarToggle) return;
        
        // Handle clicks outside sidebar on mobile
        body.addEventListener('click', (e) => {
            if (!adminSidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                adminSidebar.classList.remove('show');
            }
        });
        
        // Toggle sidebar on mobile
        sidebarToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            adminSidebar.classList.toggle('show');
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const adminInterface = new AdminInterface();
    
    // Hide page loader
    const pageLoader = document.getElementById('pageLoader');
    if (pageLoader) {
        pageLoader.style.display = 'none';
    }
});

document.addEventListener("DOMContentLoaded", () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
});
