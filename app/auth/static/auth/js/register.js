const form = document.querySelector('.login-form');
const usernameInput = document.getElementById('username');
const fullnameInput = document.getElementById('name');
const passwordInput = document.getElementById('reg-password');
const confirmPasswordInput = document.getElementById('confirm-password');
const emailInput = document.getElementById('reg-email');
const phoneInput = document.getElementById('phone');

// Phone number validation patterns for different countries
const phonePatterns = {
    1: /^1[2-9]\d{9}$/, // US/Canada: 1 + area code (2-9) + 7 digits
    44: /^44[1-9]\d{8,9}$/, // UK
    33: /^33[1-9]\d{8}$/, // France
    49: /^49[1-9]\d{7,11}$/, // Germany
    91: /^91[6-9]\d{9}$/, // India
    86: /^86[1]\d{10}$/, // China
    61: /^61[2-9]\d{8}$/, // Australia
    // Add more patterns as needed
};

// Generic validation for countries not in the specific patterns
function isValidPhoneNumber(phone, countryCode) {
    // Remove any non-digit characters except +
    const cleanPhone = phone.replace(/[^\d+]/g, '');
    
    // Check if phone starts with country code
    if (!cleanPhone.startsWith('+' + countryCode) && !cleanPhone.startsWith(countryCode)) {
        return false;
    }
    
    // Remove country code for length check
    const phoneWithoutCode = cleanPhone.replace(new RegExp(`^\\+?${countryCode}`), '');
    
    // Check specific pattern if available
    if (phonePatterns[countryCode]) {
        return phonePatterns[countryCode].test(countryCode + phoneWithoutCode);
    }
    
    // Generic validation: phone should be 7-15 digits after country code
    return phoneWithoutCode.length >= 7 && phoneWithoutCode.length <= 15 && /^\d+$/.test(phoneWithoutCode);
}

function getCurrentCountryCode() {
    const selectedOption = document.querySelector('.selected-option strong');
    return selectedOption ? selectedOption.textContent.replace('+', '') : '1';
}

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
    const inputWrapper = input.closest('.input-wrapper') || input.closest('.gender-options') || input.closest('.select-box') || input.parentElement;
    inputWrapper.insertAdjacentElement('afterend', errorDiv);
}

function hideError(input) {
    const inputWrapper = input.closest('.input-wrapper') || input.closest('.gender-options') || input.closest('.select-box') || input.parentElement;
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

// Enhanced validation functions
function validateUsername(username) {
    if (!username.trim()) {
        return 'Username is required';
    }
    if (username.length < 3) {
        return 'Username must be at least 3 characters long';
    }
    if (username.length > 20) {
        return 'Username must be less than 20 characters';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        return 'Username can only contain letters, numbers, and underscores';
    }
    return null;
}

function validateFullname(fullname) {
    if (!fullname.trim()) {
        return 'Full name is required';
    }
    if (fullname.trim().length < 2) {
        return 'Full name must be at least 2 characters long';
    }
    if (!/^[a-zA-Z\s]+$/.test(fullname.trim())) {
        return 'Full name can only contain letters and spaces';
    }
    return null;
}

function validateEmail(email) {
    if (!email.trim()) {
        return 'Email is required';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return 'Please enter a valid email address';
    }
    // Additional email validation
    if (email.length > 254) {
        return 'Email address is too long';
    }
    const parts = email.split('@');
    if (parts[0].length > 64) {
        return 'Email address is invalid';
    }
    return null;
}

function validatePassword(password) {
    if (!password) {
        return 'Password is required';
    }
    if (password.length < 8) {
        return 'Password must be at least 8 characters long';
    }
    if (password.length > 128) {
        return 'Password is too long (maximum 128 characters)';
    }
    
    let hasLower = /[a-z]/.test(password);
    let hasUpper = /[A-Z]/.test(password);
    let hasNumber = /\d/.test(password);
    let hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
    
    if (!hasLower) {
        return 'Password must contain at least one lowercase letter';
    }
    if (!hasUpper) {
        return 'Password must contain at least one uppercase letter';
    }
    if (!hasNumber && !hasSpecial) {
        return 'Password must contain at least one number or special character';
    }
    
    return null;
}

function validatePhone(phone) {
    if (!phone.trim()) {
        return 'Phone number is required';
    }
    
    const countryCode = getCurrentCountryCode();
    
    // Clean the phone number
    let cleanPhone = phone.replace(/[^\d+]/g, '');
    
    // Ensure it starts with country code
    if (!cleanPhone.startsWith('+')) {
        cleanPhone = '+' + countryCode + cleanPhone.replace(new RegExp(`^${countryCode}`), '');
    }
    
    if (!isValidPhoneNumber(cleanPhone, countryCode)) {
        return `Please enter a valid phone number for the selected country (+${countryCode})`;
    }
    
    return null;
}

// Real-time validation
if (usernameInput) {
    usernameInput.addEventListener('blur', function() {
        const error = validateUsername(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
    
    usernameInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

if (fullnameInput) {
    fullnameInput.addEventListener('blur', function() {
        const error = validateFullname(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
    
    fullnameInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

if (emailInput) {
    emailInput.addEventListener('blur', function() {
        const error = validateEmail(this.value);
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
}

if (phoneInput) {
    phoneInput.addEventListener('blur', function() {
        const error = validatePhone(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
    
    phoneInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

// Enhanced password strength indicator
if (passwordInput) {
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strengthBar = document.querySelector('.strength-bar');
        const strengthText = document.querySelector('.strength-text');
        
        let strength = 0;
        let strengthLabel = 'Very Weak';
        let color = '#ff4444';
        
        if (password.length >= 8) strength += 20;
        if (password.length >= 12) strength += 10;
        if (password.match(/[a-z]/)) strength += 20;
        if (password.match(/[A-Z]/)) strength += 20;
        if (password.match(/[0-9]/)) strength += 15;
        if (password.match(/[^a-zA-Z0-9]/)) strength += 15;
        
        if (strength >= 90) {
            strengthLabel = 'Very Strong';
            color = '#0f7b0f';
        } else if (strength >= 75) {
            strengthLabel = 'Strong';
            color = '#4CAF50';
        } else if (strength >= 50) {
            strengthLabel = 'Medium';
            color = '#ff9800';
        } else if (strength >= 25) {
            strengthLabel = 'Weak';
            color = '#ff6b35';
        }
        
        strengthBar.style.width = Math.min(strength, 100) + '%';
        strengthBar.style.background = color;
        strengthText.textContent = 'Password Strength: ' + strengthLabel;
        strengthText.style.color = color;
    });
    
    passwordInput.addEventListener('blur', function() {
        const error = validatePassword(this.value);
        if (error) {
            showError(this, error);
        } else {
            showSuccess(this);
        }
    });
}

if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener('blur', function() {
        if (!this.value) {
            showError(this, 'Please confirm your password');
        } else if (passwordInput && this.value !== passwordInput.value) {
            showError(this, 'Passwords do not match');
        } else {
            showSuccess(this);
        }
    });
    
    confirmPasswordInput.addEventListener('input', function() {
        if (this.value.trim()) {
            hideError(this);
        }
    });
}

// Enhanced form submission
form.addEventListener('submit', function(e) {
    let isValid = true;
    const errors = [];
    
    // Validate all fields
    if (usernameInput) {
        const usernameError = validateUsername(usernameInput.value);
        if (usernameError) {
            showError(usernameInput, usernameError);
            errors.push('Username: ' + usernameError);
            isValid = false;
        }
    }
    
    if (fullnameInput) {
        const fullnameError = validateFullname(fullnameInput.value);
        if (fullnameError) {
            showError(fullnameInput, fullnameError);
            errors.push('Full name: ' + fullnameError);
            isValid = false;
        }
    }
    
    if (emailInput) {
        const emailError = validateEmail(emailInput.value);
        if (emailError) {
            showError(emailInput, emailError);
            errors.push('Email: ' + emailError);
            isValid = false;
        }
    }
    
    if (passwordInput) {
        const passwordError = validatePassword(passwordInput.value);
        if (passwordError) {
            showError(passwordInput, passwordError);
            errors.push('Password: ' + passwordError);
            isValid = false;
        }
    }
    
    if (confirmPasswordInput) {
        if (!confirmPasswordInput.value) {
            showError(confirmPasswordInput, 'Please confirm your password');
            errors.push('Confirm password is required');
            isValid = false;
        } else if (passwordInput && confirmPasswordInput.value !== passwordInput.value) {
            showError(confirmPasswordInput, 'Passwords do not match');
            errors.push('Passwords do not match');
            isValid = false;
        }
    }
    
    if (phoneInput) {
        const phoneError = validatePhone(phoneInput.value);
        if (phoneError) {
            showError(phoneInput, phoneError);
            errors.push('Phone: ' + phoneError);
            isValid = false;
        }
    }
    
    // Check gender selection
    const genderSelected = document.querySelector('input[name="gender"]:checked');
    if (!genderSelected) {
        const genderContainer = document.querySelector('.gender-options');
        showError(genderContainer, 'Please select a gender');
        errors.push('Gender selection is required');
        isValid = false;
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