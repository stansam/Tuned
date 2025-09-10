// Global variables
let isLoading = false;

// Modal functions
function openProfileModal() {
    const modal = document.getElementById('profileModal');
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    loadUserData();
}

function closeProfileModal() {
    const modal = document.getElementById('profileModal');
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
    clearForm();
}

// Load current user data
async function loadUserData() {
    try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: 'GET',
            credentials: include,
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const userData = await response.json();
            populateForm(userData);
        } else {
            console.error('Failed to load user data');
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Populate form with user data
function populateForm(userData) {
    document.getElementById('firstName').value = userData.first_name || '';
    document.getElementById('lastName').value = userData.last_name || '';
    document.getElementById('username').value = userData.username || '';
    document.getElementById('email').value = userData.email || '';
    document.getElementById('gender').value = userData.gender || '';
}

// Clear form and errors
function clearForm() {
    document.getElementById('profileForm').reset();
    clearErrors();
    hideSuccessMessage();
}

// Clear all error messages
function clearErrors() {
    const errorMessages = document.querySelectorAll('.error-message');
    const inputs = document.querySelectorAll('input, select');
    
    errorMessages.forEach(error => {
        error.classList.remove('show');
        error.textContent = '';
    });
    
    inputs.forEach(input => {
        input.classList.remove('error');
    });
}

// Show error for specific field
function showError(fieldName, message) {
    const errorElement = document.getElementById(fieldName + 'Error');
    const inputElement = document.getElementById(fieldName);
    
    if (errorElement && inputElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
        inputElement.classList.add('error');
    }
}

// Show success message
function showSuccessMessage() {
    const successMessage = document.getElementById('successMessage');
    successMessage.classList.add('show');
    setTimeout(hideSuccessMessage, 3000);
}

// Hide success message
function hideSuccessMessage() {
    const successMessage = document.getElementById('successMessage');
    successMessage.classList.remove('show');
}

// Set loading state
function setLoading(loading) {
    isLoading = loading;
    const saveBtn = document.getElementById('saveBtn');
    
    if (loading) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner"></span>Saving...';
    } else {
        saveBtn.disabled = false;
        saveBtn.innerHTML = 'Save Changes';
    }
}

// Form submission
document.getElementById('profileForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    if (isLoading) return;
    
    clearErrors();
    setLoading(true);
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch(`${API_BASE_URL}/profile`, {
            method: 'PUT',
            credentials: include,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccessMessage();
            setTimeout(() => {
                closeProfileModal();
            }, 1500);
        } else {
            // Handle validation errors
            if (result.errors) {
                Object.keys(result.errors).forEach(field => {
                    showError(field, result.errors[field]);
                });
            } else {
                alert(result.message || 'An error occurred while updating your profile.');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Network error. Please try again.');
    } finally {
        setLoading(false);
    }
});

// Close modal when clicking outside
document.getElementById('profileModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeProfileModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('profileModal').classList.contains('active')) {
        closeProfileModal();
    }
});

// Real-time validation
document.getElementById('email').addEventListener('blur', function() {
    const email = this.value;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        showError('email', 'Please enter a valid email address.');
    }
});

document.getElementById('username').addEventListener('blur', function() {
    const username = this.value;
    
    if (username && username.length < 3) {
        showError('username', 'Username must be at least 3 characters long.');
    }
});