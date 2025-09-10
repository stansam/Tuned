const form = document.querySelector('.login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');

form.addEventListener('submit', function(e) {
    // e.preventDefault();
    
    let isValid = true;
    
    // Validate email
    if (!emailInput.value.trim()) {
        emailInput.style.borderColor = '#ff4444';
        isValid = false;
    } else {
        emailInput.style.borderColor = '#4CAF50';
    }
    
    // Validate password
    if (!passwordInput.value.trim()) {
        passwordInput.style.borderColor = '#ff4444';
        isValid = false;
    } else {
        passwordInput.style.borderColor = '#4CAF50';
    }
    
    if (!isValid) {
        e.preventDefault();
    }
});