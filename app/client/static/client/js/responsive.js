// Responsive Layout JavaScript
class ResponsiveLayout {
    constructor() {
        this.sidebar = null;
        this.sidebarOverlay = null;
        this.mobileMenuToggle = null;
        this.profileDropdown = null;
        this.profileItem = null;
        this.isProfileDropdownOpen = false;
        this.isMobileMenuOpen = false;
        this.breakpoints = {
            mobile: 768,
            tablet: 992,
            desktop: 1200
        };
        
        this.init();
    }

    init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        this.cacheElements();
        this.bindEvents();
        this.handleResize();
        
        // Initial setup
        this.updateLayoutForScreenSize();
    }

    cacheElements() {
        this.sidebar = document.querySelector('.sidebar');
        this.sidebarOverlay = document.querySelector('.sidebar-overlay');
        this.mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        this.profileDropdown = document.querySelector('.profile-dropdown');
        this.profileItem = document.querySelector('.profile-item');
    }

    bindEvents() {
        // Mobile menu toggle
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMobileMenu();
            });
        }

        // Sidebar overlay click to close
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }

        // Profile dropdown toggle
        if (this.profileItem) {
            this.profileItem.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleProfileDropdown();
            });
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isProfileDropdownOpen && !this.profileItem?.contains(e.target)) {
                this.closeProfileDropdown();
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (this.isMobileMenuOpen) {
                    this.closeMobileMenu();
                }
                if (this.isProfileDropdownOpen) {
                    this.closeProfileDropdown();
                }
            }
        });

        // Window resize handler
        window.addEventListener('resize', () => this.handleResize());

        // Prevent body scroll when mobile menu is open
        document.addEventListener('touchmove', (e) => {
            if (this.isMobileMenuOpen && !this.sidebar?.contains(e.target)) {
                e.preventDefault();
            }
        }, { passive: false });
    }

    toggleMobileMenu() {
        if (this.isMobileMenuOpen) {
            this.closeMobileMenu();
        } else {
            this.openMobileMenu();
        }
    }

    openMobileMenu() {
        if (!this.sidebar || !this.sidebarOverlay) return;
        
        this.sidebar.classList.add('show');
        this.sidebarOverlay.classList.add('show');
        this.isMobileMenuOpen = true;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Focus trap for accessibility
        this.trapFocus(this.sidebar);
        
        // Announce to screen readers
        this.announceToScreenReader('Navigation menu opened');
    }

    closeMobileMenu() {
        if (!this.sidebar || !this.sidebarOverlay) return;
        
        this.sidebar.classList.remove('show');
        this.sidebarOverlay.classList.remove('show');
        this.isMobileMenuOpen = false;
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Return focus to toggle button
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.focus();
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Navigation menu closed');
    }

    toggleProfileDropdown() {
        if (this.isProfileDropdownOpen) {
            this.closeProfileDropdown();
        } else {
            this.openProfileDropdown();
        }
    }

    openProfileDropdown() {
        if (!this.profileDropdown) return;
        
        this.profileDropdown.style.display = 'block';
        
        // Force reflow for animation
        this.profileDropdown.offsetHeight;
        
        this.profileDropdown.classList.add('show');
        this.isProfileDropdownOpen = true;
        
        // Focus first item for accessibility
        const firstItem = this.profileDropdown.querySelector('.dropdown-item');
        if (firstItem) {
            firstItem.focus();
        }
        
        this.announceToScreenReader('Profile menu opened');
    }

    closeProfileDropdown() {
        if (!this.profileDropdown) return;
        
        this.profileDropdown.classList.remove('show');
        this.isProfileDropdownOpen = false;
        
        // Hide after animation
        setTimeout(() => {
            if (!this.isProfileDropdownOpen) {
                this.profileDropdown.style.display = 'none';
            }
        }, 200);
        
        this.announceToScreenReader('Profile menu closed');
    }

    handleResize() {
        // Debounce resize events
        clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(() => {
            this.updateLayoutForScreenSize();
        }, 100);
    }

    updateLayoutForScreenSize() {
        const windowWidth = window.innerWidth;
        
        // Close mobile menu on desktop
        if (windowWidth >= this.breakpoints.mobile && this.isMobileMenuOpen) {
            this.closeMobileMenu();
        }
        
        // Close profile dropdown on very small screens
        if (windowWidth < 320 && this.isProfileDropdownOpen) {
            this.closeProfileDropdown();
        }
        
        // Update ARIA attributes based on screen size
        this.updateAriaAttributes(windowWidth);
    }

    updateAriaAttributes(windowWidth) {
        if (this.sidebar) {
            if (windowWidth < this.breakpoints.mobile) {
                this.sidebar.setAttribute('aria-hidden', this.isMobileMenuOpen ? 'false' : 'true');
            } else {
                this.sidebar.removeAttribute('aria-hidden');
            }
        }
        
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.setAttribute('aria-expanded', this.isMobileMenuOpen.toString());
        }
    }

    trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select'
        );
        
        const firstFocusableElement = focusableElements[0];
        const lastFocusableElement = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusableElement) {
                        lastFocusableElement.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastFocusableElement) {
                        firstFocusableElement.focus();
                        e.preventDefault();
                    }
                }
            }
        });
        
        // Focus first element
        if (firstFocusableElement) {
            firstFocusableElement.focus();
        }
    }

    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // Public method to programmatically close menus
    closeAllMenus() {
        this.closeMobileMenu();
        this.closeProfileDropdown();
    }

    // Public method to get current breakpoint
    getCurrentBreakpoint() {
        const windowWidth = window.innerWidth;
        
        if (windowWidth < this.breakpoints.mobile) {
            return 'mobile';
        } else if (windowWidth < this.breakpoints.tablet) {
            return 'tablet';
        } else if (windowWidth < this.breakpoints.desktop) {
            return 'desktop';
        } else {
            return 'large-desktop';
        }
    }

    // Public method for external components to listen to breakpoint changes
    onBreakpointChange(callback) {
        let currentBreakpoint = this.getCurrentBreakpoint();
        
        const checkBreakpoint = () => {
            const newBreakpoint = this.getCurrentBreakpoint();
            if (newBreakpoint !== currentBreakpoint) {
                currentBreakpoint = newBreakpoint;
                callback(newBreakpoint);
            }
        };
        
        window.addEventListener('resize', checkBreakpoint);
        
        // Return unsubscribe function
        return () => window.removeEventListener('resize', checkBreakpoint);
    }
}

// Utility functions for smooth scrolling and animations
class UIAnimations {
    static smoothScrollTo(element, duration = 300) {
        const targetPosition = element.offsetTop;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = UIAnimations.easeInOutQuad(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        }

        requestAnimationFrame(animation);
    }

    static easeInOutQuad(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    static fadeIn(element, duration = 300) {
        element.style.opacity = 0;
        element.style.display = 'block';
        
        const start = performance.now();
        
        function fade(currentTime) {
            const elapsed = currentTime - start;
            const progress = elapsed / duration;
            
            if (progress < 1) {
                element.style.opacity = progress;
                requestAnimationFrame(fade);
            } else {
                element.style.opacity = 1;
            }
        }
        
        requestAnimationFrame(fade);
    }

    static fadeOut(element, duration = 300) {
        const start = performance.now();
        const startOpacity = parseFloat(window.getComputedStyle(element).opacity);
        
        function fade(currentTime) {
            const elapsed = currentTime - start;
            const progress = elapsed / duration;
            
            if (progress < 1) {
                element.style.opacity = startOpacity * (1 - progress);
                requestAnimationFrame(fade);
            } else {
                element.style.opacity = 0;
                element.style.display = 'none';
            }
        }
        
        requestAnimationFrame(fade);
    }
}

// Touch gesture support for mobile
class TouchGestures {
    constructor(layout) {
        this.layout = layout;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.isDragging = false;
        this.threshold = 50; // Minimum distance for swipe
        
        this.bindTouchEvents();
    }

    bindTouchEvents() {
        document.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        document.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: true });
        document.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
    }

    handleTouchStart(e) {
        const touch = e.touches[0];
        this.startX = touch.clientX;
        this.startY = touch.clientY;
        this.isDragging = true;
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;
        
        const touch = e.touches[0];
        this.currentX = touch.clientX;
        this.currentY = touch.clientY;
    }

    handleTouchEnd(e) {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        
        const deltaX = this.currentX - this.startX;
        const deltaY = this.currentY - this.startY;
        
        // Check if it's a horizontal swipe
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > this.threshold) {
            if (deltaX > 0 && this.startX < 50) {
                // Swipe right from left edge - open menu
                this.layout.openMobileMenu();
            } else if (deltaX < 0 && this.layout.isMobileMenuOpen) {
                // Swipe left when menu is open - close menu
                this.layout.closeMobileMenu();
            }
        }
        
        // Reset values
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
    }
}

// Initialize the responsive layout when the script loads
let responsiveLayout;
let touchGestures;

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    responsiveLayout = new ResponsiveLayout();
    touchGestures = new TouchGestures(responsiveLayout);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ResponsiveLayout, UIAnimations, TouchGestures };
}

// Global access
window.ResponsiveLayout = ResponsiveLayout;
window.UIAnimations = UIAnimations;
window.TouchGestures = TouchGestures;
