let profilePicFile = null;
let profilePicPreviewUrl = null;
let isUploadingProfilePic = false;

function initializeProfilePicUpload() {
    const profilePicInput = document.getElementById('profilePicInput');
    const profilePicPreview = document.getElementById('profilePicPreview');
    
    if (!profilePicInput || !profilePicPreview) {
        console.error('Profile picture elements not found');
        return;
    }

    profilePicInput.addEventListener('change', handleProfilePicSelection);
    
    addRemovePictureButton();
    
    loadCurrentProfilePicture();
}

function handleProfilePicSelection(event) {
    const file = event.target.files[0];
    
    if (!file) {
        resetProfilePicPreview();
        return;
    }
    
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

function validateProfilePicFile(file) {
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
        return {
            isValid: false,
            message: 'File size too large. Maximum size: 5.0MB'
        };
    }
    
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        return {
            isValid: false,
            message: 'File type not allowed. Allowed types: JPEG, PNG, GIF, WebP'
        };
    }
    
    return { isValid: true };
}

function previewProfilePicture(file) {
    const reader = new FileReader();
    const profilePicPreview = document.getElementById('profilePicPreview');
    
    reader.onload = function(e) {
        profilePicPreviewUrl = e.target.result;
        profilePicPreview.src = profilePicPreviewUrl;
        profilePicPreview.style.opacity = '1';
        
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
                'X-CSRF-Token': document.getElementById('csrfTokenMeta').getAttribute('content')
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const profilePicPreview = document.getElementById('profilePicPreview');
            profilePicPreview.src = result.data.profile_pic_url;
            
            showProfilePicSuccess('Profile picture updated successfully!');
            
            resetProfilePicInput();
            hideUploadButton();
            
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

async function removeProfilePicture() {
    if (isUploadingProfilePic) {
        return false;
    }
    
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
                'X-CSRF-Token': document.getElementById('csrfTokenMeta').getAttribute('content'),
                
            }
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            const profilePicPreview = document.getElementById('profilePicPreview');
            profilePicPreview.src = result.data.profile_pic_url;
            
            showProfilePicSuccess('Profile picture removed successfully!');
            
            resetProfilePicInput();
            hideUploadButton();
            hideRemoveButton();
            
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

function loadCurrentProfilePicture() {
}

function populateFormWithProfilePic(userData) {
    if (typeof populateForm === 'function') {
        populateForm(userData);
    }
    
    const profilePicPreview = document.getElementById('profilePicPreview');
    if (profilePicPreview && userData.profile_pic_url) {
        profilePicPreview.src = userData.profile_pic_url;
        
        if (userData.profile_pic && userData.profile_pic !== 'default.png') {
            showRemoveButton();
        } else {
            hideRemoveButton();
        }
    }
}

function addRemovePictureButton() {
    const profilePicActions = document.querySelector('.profile-pic-actions');
    if (!profilePicActions) return;
    
    if (document.getElementById('removePicBtn')) return;
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.id = 'removePicBtn';
    removeBtn.className = 'profile-btn-remove';
    removeBtn.textContent = 'Remove Picture';
    removeBtn.style.display = 'none';
    removeBtn.onclick = removeProfilePicture;
    
    profilePicActions.appendChild(removeBtn);
    
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

function resetProfilePicInput() {
    const profilePicInput = document.getElementById('profilePicInput');
    if (profilePicInput) {
        profilePicInput.value = '';
    }
    profilePicFile = null;
    profilePicPreviewUrl = null;
}

function resetProfilePicPreview() {
    const profilePicPreview = document.getElementById('profilePicPreview');
    if (profilePicPreview && profilePicPreview.dataset.originalSrc) {
        profilePicPreview.src = profilePicPreview.dataset.originalSrc;
    }
    hideUploadButton();
}

function showProfilePicError(message) {
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

function showProfilePicSuccess(message) {
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
    
    setTimeout(() => {
        successElement.classList.remove('show');
    }, 3000);
}

function clearProfilePicError() {
    const errorElement = document.getElementById('profilePicError');
    if (errorElement) {
        errorElement.classList.remove('show');
        errorElement.textContent = '';
    }
}

function updateAllProfilePictures(newUrl) {
    const profilePics = document.querySelectorAll('img[alt*="Profile"], .profile-pic, .user-avatar');
    profilePics.forEach(img => {
        if (img.src !== newUrl) {
            img.src = newUrl;
        }
    });
}

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

document.addEventListener('DOMContentLoaded', function() {
    initializeProfilePicUpload();
});

const originalOpenProfileModal = window.openProfileModal;
window.openProfileModal = function() {
    if (originalOpenProfileModal) {
        originalOpenProfileModal();
    }
    setTimeout(() => {
        initializeProfilePicUpload();
    }, 100);
};

const originalCloseProfileModal = window.closeProfileModal;
window.closeProfileModal = function() {
    clearProfilePicForm();
    
    if (originalCloseProfileModal) {
        originalCloseProfileModal();
    }
};

const originalClearForm = window.clearForm;
window.clearForm = function() {
    if (originalClearForm) {
        originalClearForm();
    }
    clearProfilePicForm();
};

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
                profilePicInput.files = files;
                const event = new Event('change', { bubbles: true });
                profilePicInput.dispatchEvent(event);
            }
        }
    });
}

setTimeout(() => {
    initializeDragAndDrop();
}, 200);