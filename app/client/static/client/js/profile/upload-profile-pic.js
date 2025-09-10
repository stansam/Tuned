// Profile Picture Upload Functionality
// This script handles profile picture upload, preview, and removal

// Global variables for profile picture functionality
let profilePicFile = null;
let profilePicPreviewUrl = null;
let isUploadingProfilePic = false;

// Initialize profile picture functionality
function initializeProfilePicUpload() {
    const profilePicInput = document.getElementById('profilePicInput');
    const profilePicPreview = document.getElementById('profilePicPreview');
    
    if (!profilePicInput || !profilePicPreview) {
        console.error('Profile picture elements not found');
        return;
    }

    // Handle file input change
    profilePicInput.addEventListener('change', handleProfilePicSelection);
    
    // Add remove picture button if it doesn't exist
    addRemovePictureButton();
    
    // Load current profile picture when modal opens
    loadCurrentProfilePicture();
}

// Handle profile picture file selection
function handleProfilePicSelection(event) {
    const file = event.target.files[0];
    
    if (!file) {
        resetProfilePicPreview();
        return;
    }
    
    // Validate file before preview
    const validation = validateProfilePicFile(file);
    if (!validation.isValid) {
        showProfilePicError(validation.message);
        resetProfilePicInput();
        return;
    }
    
    profilePicFile = file;
    previewProfilePicture(file);
    clearProfilePicError();
}

// Validate profile picture file
function validateProfilePicFile(file) {
    // Check file size (5MB limit based on your config)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        return {
            isValid: false,
            message: 'File size too large. Maximum size: 5.0MB'
        };
    }
    
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        return {
            isValid: false,
            message: 'File type not allowed. Allowed types: JPEG, PNG, GIF, WebP'
        };
    }
    
    return { isValid: true };
}

// Preview selected profile picture
function previewProfilePicture(file) {
    const reader = new FileReader();
    const profilePicPreview = document.getElementById('profilePicPreview');
    
    reader.onload = function(e) {
        profilePicPreviewUrl = e.target.result;
        profilePicPreview.src = profilePicPreviewUrl;
        profilePicPreview.style.opacity = '1';
        
        // Show upload button
        showUploadButton();
    };
    
    reader.onerror = function() {
        showProfilePicError('Error reading file. Please try again.');
        resetProfilePicInput();
    };
    
    reader.readAsDataURL(file);
}

// Upload profile picture to server
async function uploadProfilePicture() {
    if (!profilePicFile) {
        showProfilePicError('Please select a file first.');
        return false;
    }
    
    if (isUploadingProfilePic) {
        return false;
    }
    
    setProfilePicUploadLoading(true);
    clearProfilePicError();
    
    const formData = new FormData();
    formData.append('profile_pic', profilePicFile);
    
    try {
        const response = await fetch(`${API_BASE_URL}/profile/upload-picture`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'X-CSRF-Token': document.getElementById('csrfToken').value
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Update preview with server URL
            const profilePicPreview = document.getElementById('profilePicPreview');
            profilePicPreview.src = result.data.profile_pic_url;
            
            // Show success message
            showProfilePicSuccess('Profile picture updated successfully!');
            
            // Reset file input and hide upload button
            resetProfilePicInput();
            hideUploadButton();
            
            // Update any other profile pictures on the page
            updateAllProfilePictures(result.data.profile_pic_url);
            
            return true;
        } else {
            throw new Error(result.message || 'Failed to upload profile picture');
        }
    } catch (error) {
        console.error('Error uploading profile picture:', error);
        showProfilePicError(error.message || 'Failed to upload profile picture. Please try again.');
        return false;
    } finally {
        setProfilePicUploadLoading(false);
    }
}

// Remove profile picture
async function removeProfilePicture() {
    if (isUploadingProfilePic) {
        return false;
    }
    
    // Confirm removal
    if (!confirm('Are you sure you want to remove your profile picture?')) {
        return false;
    }
    
    setProfilePicUploadLoading(true);
    clearProfilePicError();
    
    try {
        const response = await fetch(`${API_BASE_URL}/profile/remove-picture`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Update preview with default image
            const profilePicPreview = document.getElementById('profilePicPreview');
            profilePicPreview.src = result.data.profile_pic_url;
            
            // Show success message
            showProfilePicSuccess('Profile picture removed successfully!');
            
            // Reset file input and hide buttons
            resetProfilePicInput();
            hideUploadButton();
            hideRemoveButton();
            
            // Update any other profile pictures on the page
            updateAllProfilePictures(result.data.profile_pic_url);
            
            return true;
        } else {
            throw new Error(result.message || 'Failed to remove profile picture');
        }
    } catch (error) {
        console.error('Error removing profile picture:', error);
        showProfilePicError(error.message || 'Failed to remove profile picture. Please try again.');
        return false;
    } finally {
        setProfilePicUploadLoading(false);
    }
}

// Load current profile picture when modal opens
function loadCurrentProfilePicture() {
    // This function integrates with your existing loadUserData function
    // We'll modify the populateForm function to also update the profile picture
}

// Enhanced populateForm function (to be used with your existing one)
function populateFormWithProfilePic(userData) {
    // Call your existing populateForm function
    if (typeof populateForm === 'function') {
        populateForm(userData);
    }
    
    // Update profile picture
    const profilePicPreview = document.getElementById('profilePicPreview');
    if (profilePicPreview && userData.profile_pic_url) {
        profilePicPreview.src = userData.profile_pic_url;
        
        // Show remove button if not default picture
        if (userData.profile_pic && userData.profile_pic !== 'default.png') {
            showRemoveButton();
        } else {
            hideRemoveButton();
        }
    }
}

// Add remove picture button dynamically
function addRemovePictureButton() {
    const profilePicActions = document.querySelector('.profile-pic-actions');
    if (!profilePicActions) return;
    
    // Check if remove button already exists
    if (document.getElementById('removePicBtn')) return;
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.id = 'removePicBtn';
    removeBtn.className = 'profile-btn-remove';
    removeBtn.textContent = 'Remove Picture';
    removeBtn.style.display = 'none';
    removeBtn.onclick = removeProfilePicture;
    
    profilePicActions.appendChild(removeBtn);
    
    // Add upload button if it doesn't exist
    if (!document.getElementById('uploadPicBtn')) {
        const uploadBtn = document.createElement('button');
        uploadBtn.type = 'button';
        uploadBtn.id = 'uploadPicBtn';
        uploadBtn.className = 'profile-btn-upload-action';
        uploadBtn.textContent = 'Upload Selected';
        uploadBtn.style.display = 'none';
        uploadBtn.onclick = uploadProfilePicture;
        
        profilePicActions.appendChild(uploadBtn);
    }
}

// Show/Hide upload button
function showUploadButton() {
    const uploadBtn = document.getElementById('uploadPicBtn');
    if (uploadBtn) {
        uploadBtn.style.display = 'inline-block';
    }
}

function hideUploadButton() {
    const uploadBtn = document.getElementById('uploadPicBtn');
    if (uploadBtn) {
        uploadBtn.style.display = 'none';
    }
}

// Show/Hide remove button
function showRemoveButton() {
    const removeBtn = document.getElementById('removePicBtn');
    if (removeBtn) {
        removeBtn.style.display = 'inline-block';
    }
}

function hideRemoveButton() {
    const removeBtn = document.getElementById('removePicBtn');
    if (removeBtn) {
        removeBtn.style.display = 'none';
    }
}

// Set loading state for profile picture operations
function setProfilePicUploadLoading(loading) {
    isUploadingProfilePic = loading;
    const uploadBtn = document.getElementById('uploadPicBtn');
    const removeBtn = document.getElementById('removePicBtn');
    const profilePicInput = document.getElementById('profilePicInput');
    
    if (loading) {
        if (uploadBtn) {
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<span class="spinner"></span>Uploading...';
        }
        if (removeBtn) {
            removeBtn.disabled = true;
        }
        if (profilePicInput) {
            profilePicInput.disabled = true;
        }
    } else {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = 'Upload Selected';
        }
        if (removeBtn) {
            removeBtn.disabled = false;
        }
        if (profilePicInput) {
            profilePicInput.disabled = false;
        }
    }
}

// Reset profile picture input
function resetProfilePicInput() {
    const profilePicInput = document.getElementById('profilePicInput');
    if (profilePicInput) {
        profilePicInput.value = '';
    }
    profilePicFile = null;
    profilePicPreviewUrl = null;
}

// Reset profile picture preview to current/default
function resetProfilePicPreview() {
    const profilePicPreview = document.getElementById('profilePicPreview');
    if (profilePicPreview && profilePicPreview.dataset.originalSrc) {
        profilePicPreview.src = profilePicPreview.dataset.originalSrc;
    }
    hideUploadButton();
}

// Show profile picture error
function showProfilePicError(message) {
    // Create error element if it doesn't exist
    let errorElement = document.getElementById('profilePicError');
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.id = 'profilePicError';
        errorElement.className = 'error-message profile-pic-error';
        
        const profilePicSection = document.querySelector('.profile-pic-section');
        if (profilePicSection) {
            profilePicSection.appendChild(errorElement);
        }
    }
    
    errorElement.textContent = message;
    errorElement.classList.add('show');
}

// Show profile picture success
function showProfilePicSuccess(message) {
    // Create success element if it doesn't exist
    let successElement = document.getElementById('profilePicSuccess');
    if (!successElement) {
        successElement = document.createElement('div');
        successElement.id = 'profilePicSuccess';
        successElement.className = 'success-message profile-pic-success';
        
        const profilePicSection = document.querySelector('.profile-pic-section');
        if (profilePicSection) {
            profilePicSection.appendChild(successElement);
        }
    }
    
    successElement.textContent = message;
    successElement.classList.add('show');
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        successElement.classList.remove('show');
    }, 3000);
}

// Clear profile picture error
function clearProfilePicError() {
    const errorElement = document.getElementById('profilePicError');
    if (errorElement) {
        errorElement.classList.remove('show');
        errorElement.textContent = '';
    }
}

// Update all profile pictures on the page
function updateAllProfilePictures(newUrl) {
    const profilePics = document.querySelectorAll('img[alt*="Profile"], .profile-pic, .user-avatar');
    profilePics.forEach(img => {
        if (img.src !== newUrl) {
            img.src = newUrl;
        }
    });
}

// Enhanced clear form function (extends your existing one)
function clearProfilePicForm() {
    resetProfilePicInput();
    resetProfilePicPreview();
    hideUploadButton();
    clearProfilePicError();
    
    const successElement = document.getElementById('profilePicSuccess');
    if (successElement) {
        successElement.classList.remove('show');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile picture functionality
    initializeProfilePicUpload();
});

// Hook into existing modal functions
// Extend your existing openProfileModal function
const originalOpenProfileModal = window.openProfileModal;
window.openProfileModal = function() {
    if (originalOpenProfileModal) {
        originalOpenProfileModal();
    }
    // Initialize profile pic functionality when modal opens
    setTimeout(() => {
        initializeProfilePicUpload();
    }, 100);
};

// Extend your existing closeProfileModal function
const originalCloseProfileModal = window.closeProfileModal;
window.closeProfileModal = function() {
    // Clear profile pic form
    clearProfilePicForm();
    
    if (originalCloseProfileModal) {
        originalCloseProfileModal();
    }
};

// Extend your existing clearForm function
const originalClearForm = window.clearForm;
window.clearForm = function() {
    if (originalClearForm) {
        originalClearForm();
    }
    clearProfilePicForm();
};

// Handle drag and drop functionality (bonus feature)
function initializeDragAndDrop() {
    const profilePicWrapper = document.querySelector('.profile-pic-wrapper');
    if (!profilePicWrapper) return;
    
    profilePicWrapper.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('drag-over');
    });
    
    profilePicWrapper.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
    });
    
    profilePicWrapper.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const profilePicInput = document.getElementById('profilePicInput');
            if (profilePicInput) {
                // Create a new FileList with the dropped file
                profilePicInput.files = files;
                // Trigger the change event
                const event = new Event('change', { bubbles: true });
                profilePicInput.dispatchEvent(event);
            }
        }
    });
}

// Initialize drag and drop when modal opens
setTimeout(() => {
    initializeDragAndDrop();
}, 200);