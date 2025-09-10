const form = document.querySelector('.login-form');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('reg-password');
const confirmPasswordInput = document.getElementById('confirm-password');
const emailInput = document.getElementById('reg-email');
const phoneInput = document.getElementById('phone');

if (passwordInput) {
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strengthBar = document.querySelector('.strength-bar');
        const strengthText = document.querySelector('.strength-text');
        
        let strength = 0;
        let strengthLabel = 'Weak';
        let color = '#ff4444';
        
        if (password.length >= 8) strength += 25;
        if (password.match(/[a-z]/)) strength += 25;
        if (password.match(/[A-Z]/)) strength += 25;
        if (password.match(/[0-9]/) || password.match(/[^a-zA-Z0-9]/)) strength += 25;
        
        if (strength >= 75) {
            strengthLabel = 'Strong';
            color = '#4CAF50';
        } else if (strength >= 50) {
            strengthLabel = 'Medium';
            color = '#ff9800';
        }
        
        strengthBar.style.width = strength + '%';
        strengthBar.style.background = color;
        strengthText.textContent = 'Password Strength: ' + strengthLabel;
        strengthText.style.color = color;
    });
}

form.addEventListener('submit', function(e) {    
    let isValid = true;
    const requiredFields = [usernameInput, passwordInput, confirmPasswordInput, emailInput, phoneInput];
    
    // Validate required fields
    requiredFields.forEach(field => {
        if (field && !field.value.trim()) {
            field.style.borderColor = '#ff4444';
            isValid = false;
        } else if (field) {
            field.style.borderColor = '#4CAF50';
        }
    });
    
    // Check password match
    if (passwordInput && confirmPasswordInput) {
        if (passwordInput.value !== confirmPasswordInput.value) {
            confirmPasswordInput.style.borderColor = '#ff4444';
            alert('Passwords do not match!');
            isValid = false;
        }
    }
    
    // Validate email format
    if (emailInput && emailInput.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailInput.value)) {
            emailInput.style.borderColor = '#ff4444';
            alert('Please enter a valid email address!');
            isValid = false;
        }
    }
    
    // Check gender selection
    const genderSelected = document.querySelector('input[name="gender"]:checked');
    if (!genderSelected) {
        alert('Please select a gender!');
        isValid = false;
    }
    
    if (!isValid) {
        e.preventDefault();
    }
});