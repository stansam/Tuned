const form = document.querySelector('.login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');

function showError(input, message) {
    // Remove any existing error
    hideError(input);
    
    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    
    // Add error styling to input
    input.style.borderColor = '#ff4444';
    input.style.boxShadow = '0 0 5px rgba(255, 68, 68, 0.3)';
    
    // Insert error message after the input wrapper
    const inputWrapper = input.closest('.input-wrapper') || input.parentElement;
    inputWrapper.insertAdjacentElement('afterend', errorDiv);
}

function hideError(input) {
    const inputWrapper = input.closest('.input-wrapper') || input.parentElement;
    const existingError = inputWrapper.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Reset input styling
    input.style.borderColor = '#e0e0e0';
    input.style.boxShadow = 'none';
}

function showSuccess(input) {
    hideError(input);
    input.style.borderColor = '#4CAF50';
    input.style.boxShadow = '0 0 5px rgba(76, 175, 80, 0.3)';
}

function validateEmailOrUsername(value) {
    if (!value.trim()) {
        return 'Email or username is required';
    }
    
    // Check if it's an email format
    if (value.includes('@')) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            return 'Please enter a valid email address';
        }
        if (value.length > 254) {
            return 'Email address is too long';
        }
        const parts = value.split('@');
        if (parts[0].length > 64) {
            return 'Email address is invalid';
        }
    } else {
        // Username validation
        if (value.length < 3) {
            return 'Username must be at least 3 characters long';
        }
        if (value.length > 20) {
            return 'Username must be less than 20 characters';
        }
        if (!/^[a-zA-Z0-9_]+$/.test(value)) {
            return 'Username can only contain letters, numbers, and underscores';
        }
    }
    
    return null;
}

function validatePassword(password) {
    if (!password.trim()) {
        return 'Password is required';
    }
    if (password.length < 1) {
        return 'Please enter your password';
    }
    return null;
}

// Real-time validation
if (emailInput) {
    emailInput.addEventListener('blur', function() {
        const error = validateEmailOrUsername(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
    
    emailInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
    
    // Remove error on focus
    emailInput.addEventListener('focus', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

if (passwordInput) {
    passwordInput.addEventListener('blur', function() {
        const error = validatePassword(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
    
    passwordInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
    
    // Remove error on focus
    passwordInput.addEventListener('focus', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

// Enhanced form submission
form.addEventListener('submit', function(e) {
    let isValid = true;
    const errors = [];
    
    // Validate email/username
    if (emailInput) {
        const emailError = validateEmailOrUsername(emailInput.value);
        if (emailError) {
            showError(emailInput, emailError);
            errors.push('Email/Username: ' + emailError);
            isValid = false;
        }
    }
    
    // Validate password
    if (passwordInput) {
        const passwordError = validatePassword(passwordInput.value);
        if (passwordError) {
            showError(passwordInput, passwordError);
            errors.push('Password: ' + passwordError);
            isValid = false;
        }
    }
    
    if (!isValid) {
        e.preventDefault();
        // Focus on first error field
        const firstErrorField = document.querySelector('input[style*="border-color: rgb(255, 68, 68)"]');
        if (firstErrorField) {
            firstErrorField.focus();
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
});