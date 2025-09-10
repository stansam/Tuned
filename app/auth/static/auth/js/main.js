// Input focus effects
const inputs = document.querySelectorAll('.form-input');
inputs.forEach(input => {
    input.addEventListener('focus', function() {
        this.style.borderColor = '#4CAF50';
    });
    
    input.addEventListener('blur', function() {
        if (!this.value.trim()) {
            this.style.borderColor = '#e0e0e0';
        }
    });
});

// Service tag hover effects
const tags = document.querySelectorAll('.tag');
tags.forEach(tag => {
    tag.addEventListener('click', function() {
        // Remove active class from all tags
        tags.forEach(t => t.classList.remove('popular'));
        // Add active class to clicked tag
        this.classList.add('popular');
    });
});

// Header icons click effects
const icons = document.querySelectorAll('.icon');
icons.forEach(icon => {
    icon.addEventListener('click', function() {
        this.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 150);
    });
});

// Password toggle visibility
const passwordToggle = document.querySelector('.password-toggle');
if (passwordToggle) {
    passwordToggle.addEventListener('click', function() {
        const passwordField = document.getElementById('reg-password');
        const icon = this.querySelector('i');

        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            passwordField.type = 'password';
            // this.textContent = '👁️';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".auth-alert");

    alerts.forEach(alert => {
        // trigger slide-in
        setTimeout(() => alert.classList.add("show"), 100);

        // remove after 4 seconds
        setTimeout(() => {
        alert.classList.remove("show");
        // fully remove from DOM after transition
        setTimeout(() => alert.remove(), 600);
        }, 4000);
    });
});