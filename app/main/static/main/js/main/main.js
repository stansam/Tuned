document.addEventListener('DOMContentLoaded', function() {
     // Utility: Throttle function
    function throttle(func, limit) {
        let lastFunc;
        let lastRan;
        return function() {
            const context = this;
            const args = arguments;
            if (!lastRan) {
                func.apply(context, args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(function() {
                    if ((Date.now() - lastRan) >= limit) {
                        func.apply(context, args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        };
    }

    // Back to top button functionality
    // const backToTopButton = document.querySelector('.back-to-top');
    
    // if (backToTopButton) {
    //     // Throttled show/hide back to top button
    //     window.addEventListener('scroll', throttle(function() {
    //         if (window.pageYOffset > 300) {
    //             backToTopButton.classList.add('show');
    //         } else {
    //             backToTopButton.classList.remove('show');
    //         }
    //     }, 100));

    //     // Smooth scroll to top when button is clicked
    //     backToTopButton.addEventListener('click', function(e) {
    //         e.preventDefault();
    //         window.scrollTo({
    //             top: 0,
    //             behavior: 'smooth'
    //         });
    //     });
    // }
    const backToTopBtn = document.getElementById("backToTop");

    // Show/hide button on scroll
    window.addEventListener("scroll", () => {
        if (window.scrollY > 200) {   // show after scrolling 200px
            backToTopBtn.style.display = "flex"; // uses flex to center icon
        } else {
            backToTopBtn.style.display = "none";
        }
    });

    // Scroll smoothly to top when clicked
    backToTopBtn.addEventListener("click", () => {
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    });

    // Back to top button functionality
    // const backToTopButton = document.querySelector('.back-to-top');
    
    // if (backToTopButton) {
    //     // Show/hide back to top button based on scroll position
    //     window.addEventListener('scroll', function() {
    //         if (window.pageYOffset > 300) {
    //             backToTopButton.classList.add('show');
    //         } else {
    //             backToTopButton.classList.remove('show');
    //         }
    //     });
        
    //     // Smooth scroll to top when button is clicked
    //     backToTopButton.addEventListener('click', function(e) {
    //         e.preventDefault();
    //         window.scrollTo({
    //             top: 0,
    //             behavior: 'smooth'
    //         });
    //     });
    // }
    const avatarBtn = document.getElementById('avatarBtn');
    const avatarDropdown = document.getElementById('avatarDropdown');

    if(avatarBtn){
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            avatarDropdown.classList.toggle('show');
        });
    
        document.addEventListener('click', () => {
            avatarDropdown.classList.remove('show');
        });
    }
    
    // Animate elements on scroll
    const animateElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animateElements.length > 0) {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };
        
        const observerCallback = (entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        };
        
        const observer = new IntersectionObserver(observerCallback, observerOptions);
        
        animateElements.forEach(element => {
            observer.observe(element);
        });
    }
    
    // Handle form validations
    const forms = document.querySelectorAll('.needs-validation');
    
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    if (popoverTriggerList.length > 0) {
        const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    }
 
    const faqSearch = document.getElementById('faq-search');
    const faqItems = document.querySelectorAll('.faq-item');
    
    if (faqSearch && faqItems.length > 0) {
        faqSearch.addEventListener('keyup', function() {
            const searchText = this.value.toLowerCase();
            
            faqItems.forEach(item => {
                const question = item.querySelector('.faq-question').textContent.toLowerCase();
                const answer = item.querySelector('.faq-answer').textContent.toLowerCase();
                
                if (question.includes(searchText) || answer.includes(searchText)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // FAQ category filter
    const faqCategoryLinks = document.querySelectorAll('.faq-category-link');
    
    if (faqCategoryLinks.length > 0) {
        faqCategoryLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Remove active class from all links
                faqCategoryLinks.forEach(l => l.classList.remove('active'));
                
                // Add active class to clicked link
                this.classList.add('active');
                
                // Get category
                const category = this.dataset.category;
                
                // Show/hide FAQ items based on category
                faqItems.forEach(item => {
                    if (category === 'all' || item.dataset.faqCategory === category) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // Mobile menu functionality
    // const navbarToggler = document.querySelector('.navbar-toggler');
    // const navbarCollapse = document.querySelector('.navbar-collapse');
    
    // if (navbarToggler && navbarCollapse) {
    //     // Close mobile menu when clicking outside
    //     document.addEventListener('click', function(e) {
    //         if (navbarCollapse.classList.contains('show') && 
    //             !navbarCollapse.contains(e.target) && 
    //             !navbarToggler.contains(e.target)) {
    //             navbarToggler.click();
    //         }
    //     });
        
    //     // Close mobile menu when clicking on a nav link
    //     const navLinks = navbarCollapse.querySelectorAll('.nav-link');
    //     navLinks.forEach(link => {
    //         link.addEventListener('click', function() {
    //             if (navbarCollapse.classList.contains('show')) {
    //                 navbarToggler.click();
    //             }
    //         });
    //     });
    // }

    const menuToggle = document.getElementById("menuToggle")
    menuToggle.addEventListener('click', function() {
        navLinks.classList.toggle('active');
        
        // Change icon between bars and times
        const icon = menuToggle.querySelector('i');
        if (icon.classList.contains('fa-bars')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-times');
        } else {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    });

    // Close menu when clicking on a link
    const links = navLinks.querySelectorAll('a');
    links.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.classList.remove('active');
            const icon = menuToggle.querySelector('i');
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.navbar')) {
            navLinks.classList.remove('active');
            const icon = menuToggle.querySelector('i');
            if (icon.classList.contains('fa-times')) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    });
});