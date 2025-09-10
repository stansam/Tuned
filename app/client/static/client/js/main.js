document.addEventListener('DOMContentLoaded', function() {
    const profileItem = document.querySelector('.profile-item');
    const profileDropdown = document.querySelector('.profile-dropdown');
    let isDropdownOpen = false;

    profileItem.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        isDropdownOpen = !isDropdownOpen;
        
        if (isDropdownOpen) {
            profileDropdown.style.display = 'block';
            // setTimeout(() => {
            //     profileDropdown.classList.add('show');
            // }, 10);
            profileDropdown.offsetHeight;
            profileDropdown.classList.add('show');
        } else {
            profileDropdown.classList.remove('show');
            setTimeout(() => {
                profileDropdown.style.display = 'none';
            }, 200);
        }
    });

    document.addEventListener('click', function(e) {
        if (!profileItem.contains(e.target) && !profileDropdown.contains(e.target)) {
            if (isDropdownOpen) {
                profileDropdown.classList.remove('show');
                setTimeout(() => {
                    profileDropdown.style.display = 'none';
                }, 200);
                isDropdownOpen = false;
            }
        }
    });

    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    let isMobileMenuOpen = false;

    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            isMobileMenuOpen = !isMobileMenuOpen;
            
            if (isMobileMenuOpen) {
                sidebar.classList.add('mobile-open');
                sidebarOverlay.classList.add('active');
                mobileToggle.classList.add('active');
                document.body.style.overflow = 'hidden';
            } else {
                closeMobileMenu();
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeMobileMenu);
    }

    function closeMobileMenu() {
        sidebar.classList.remove('mobile-open');
        sidebarOverlay.classList.remove('active');
        mobileToggle.classList.remove('active');
        document.body.style.overflow = '';
        isMobileMenuOpen = false;
    }

    // Close mobile menu when clicking sidebar links
    const sidebarItems = document.querySelectorAll('.sidebar-item:not(.profile-item)');
    sidebarItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768 && isMobileMenuOpen) {
            closeMobileMenu();
        }
    });

    const avatarBtn = document.getElementById('avatarBtn');
    const avatarDropdown = document.getElementById('avatarDropdown');

    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        avatarDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
        avatarDropdown.classList.remove('show');
    });

});
// document.addEventListener('touchstart', function() {}, {passive: true});