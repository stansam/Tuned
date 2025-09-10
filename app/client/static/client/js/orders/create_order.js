let currentStep = 1;
const totalSteps = 3;
let currentPriceData = null;

// Initialize form
document.addEventListener('DOMContentLoaded', function() {
    updateProgressBar();
    setupEventListeners();
});

function setupEventListeners() {
    // Word count to page count calculation
    document.getElementById('word_count').addEventListener('input', function() {
        const wordCount = parseInt(this.value) || 0;
        const pageCount = Math.ceil(wordCount / 275);
        document.getElementById('pageCount').textContent = pageCount;
        
        // Recalculate price if we have the required data
        if (currentStep === 3) {
            calculateAndUpdatePrice();
        }
    });

    // Date/time change listeners for deadline calculation
    document.getElementById('due_date').addEventListener('change', updateDeadlineHours);
    document.getElementById('due_time').addEventListener('change', updateDeadlineHours);

    // Report Type  toggle
    const turnitinReportBtn = document.getElementById('turnitinReport');
    const standardReportBtn = document.getElementById('standardReport');
    const reportHiddenInput = document.getElementById('report_type');

    turnitinReportBtn.addEventListener('click', () => {
        const isActive = turnitinReportBtn.classList.contains('active');

        if (isActive) {
            turnitinReportBtn.classList.remove('active');
            reportHiddenInput.value = '';
        } else {
            turnitinReportBtn.classList.add('active');
            standardReportBtn.classList.remove('active');
            reportHiddenInput.value = 'turnitin';
        }
        // turnitinReportBtn.classList.add('active');
        // standardReportBtn.classList.remove('active');
        // reportHiddenInput.value = 'turnitin'
    });

    standardReportBtn.addEventListener('click', () => {
        const isActive = standardReportBtn.classList.contains('active');

        if (isActive) {
            standardReportBtn.classList.remove('active');
            reportHiddenInput.value = '';
        } else {
            standardReportBtn.classList.add('active');
            turnitinReportBtn.classList.remove('active');
            reportHiddenInput.value = 'standard';
        }
        // standardReportBtn.classList.add('active');
        // turnitinReportBtn.classList.remove('active');
        // reportHiddenInput.value = 'standard'
    });

    // Line spacing toggle
    const singleSpacingBtn = document.getElementById('singleSpacing');
    const doubleSpacingBtn = document.getElementById('doubleSpacing');
    const spacingHiddenInput = document.getElementById('line_spacing');

    singleSpacingBtn.addEventListener('click', () => {
        singleSpacingBtn.classList.add('active');
        doubleSpacingBtn.classList.remove('active');
        spacingHiddenInput.value = 'single';
    });

    doubleSpacingBtn.addEventListener('click', () => {
        doubleSpacingBtn.classList.add('active');
        singleSpacingBtn.classList.remove('active');
        spacingHiddenInput.value = 'double';
    });

    // Sources Counter
    const decreaseBtn = document.getElementById('decreaseSources');
    const increaseBtn = document.getElementById('increaseSources');
    const sourcesDisplay = document.getElementById('sourcesCount');
    const hiddenSourcesField = document.getElementById('sources');

    let sourcesCount = 2;

    decreaseBtn.addEventListener('click', () => {
        if (sourcesCount > 0) {
            sourcesCount--;
            sourcesDisplay.textContent = sourcesCount;
            hiddenSourcesField.value = sourcesCount;
        }
    });

    increaseBtn.addEventListener('click', () => {
        sourcesCount++;
        sourcesDisplay.textContent = sourcesCount;
        hiddenSourcesField.value = sourcesCount;
    });

    // Service and level change listeners for price calculation
    document.getElementById('service').addEventListener('change', function() {
        if (currentStep === 3) {
            calculateAndUpdatePrice();
        }
    });

    document.getElementById('academic_level').addEventListener('change', function() {
        if (currentStep === 3) {
            calculateAndUpdatePrice();
        }
    });

    // File upload handling
    document.getElementById('fileInput').addEventListener('change', function() {
        const files = this.files;
        if (files.length > 0) {
            const fileUpload = document.querySelector('.file-upload');
            const displayInfo = document.createElement('div');
            displayInfo.innerHTML = `
                <div>${files.length} file(s) selected</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    ${Array.from(files).map(f => f.name).join(', ')}
                </div>
            `;
            const existingDisplay = fileUpload.querySelector('.file-display');
            if (existingDisplay) existingDisplay.remove();

            // Append the new display block
            displayInfo.classList.add('file-display');
            fileUpload.appendChild(displayInfo);
        }//<div class="file-upload-icon"><img src="{{url_for('static', filename='assets/cloud-upload-alt-solid.svg')}}"></div>
    });

}

function updateDeadlineHours() {
    const dateValue = document.getElementById('due_date').value;
    const timeValue = document.getElementById('due_time').value;
    
    if (dateValue && timeValue) {
        const deadlineDateTime = new Date(`${dateValue}T${timeValue}`);
        const now = new Date();
        const hoursUntilDeadline = (deadlineDateTime - now) / (1000 * 60 * 60);
        
        document.getElementById('deadline_hours').value = Math.max(0, hoursUntilDeadline);
        
        // Recalculate price if we're on the summary step
        if (currentStep === 3) {
            calculateAndUpdatePrice();
        }
    }
}

function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            document.getElementById(`step${currentStep}`).classList.remove('active');
            currentStep++;
            document.getElementById(`step${currentStep}`).classList.add('active');
            updateProgressBar();
            
            if (currentStep === 3) {
                updateSummary();
                calculateAndUpdatePrice();
            }
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        document.getElementById(`step${currentStep}`).classList.remove('active');
        currentStep--;
        document.getElementById(`step${currentStep}`).classList.add('active');
        updateProgressBar();
    }
}

function updateProgressBar() {
    const progress = (currentStep / totalSteps) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
}

function validateCurrentStep() {
    const currentStepElement = document.getElementById(`step${currentStep}`);
    const requiredFields = currentStepElement.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#dc3545';
            isValid = false;
        } else {
            field.style.borderColor = '#ddd';
        }
    });

    // Additional validation for deadline
    if (currentStep === 1) {
        updateDeadlineHours();
        const deadlineHours = parseFloat(document.getElementById('deadline_hours').value);
        if (deadlineHours <= 0) {
            document.getElementById('due_date').style.borderColor = '#dc3545';
            document.getElementById('due_time').style.borderColor = '#dc3545';
            alert('Deadline must be in the future.');
            isValid = false;
        }
    }

    if (!isValid) {
        alert('Please fill in all required fields correctly.');
    }

    return isValid;
}

function updateSummary() {
    // Get form values
    const service = document.getElementById('service');
    const academicLevel = document.getElementById('academic_level');
    const dueDate = document.getElementById('due_date');
    const dueTime = document.getElementById('due_time');
    const wordCount = document.getElementById('word_count');
    const title = document.getElementById('title');
    const description = document.getElementById('description');
    const citationStyle = document.getElementById('citation_style');
    const lineSpacing = document.getElementById('line_spacing');
    const reportType = document.getElementById('report_type');
    const sources = document.getElementById('sources');

    // Calculate pages
    const pages = Math.ceil(parseInt(wordCount.value) / 275) || 1;

    // Update summary display
    document.getElementById('summaryService').textContent = service.options[service.selectedIndex].text;
    document.getElementById('summaryServiceType').textContent = service.options[service.selectedIndex].text;
    document.getElementById('summaryLevel').textContent = academicLevel.options[academicLevel.selectedIndex].text;
    document.getElementById('summaryPages').textContent = pages;
    document.getElementById('summaryPaperCount').textContent = pages + ' pages';
    document.getElementById('summaryDeadline').textContent = `${dueDate.value} ${dueTime.value}`;
    document.getElementById('summaryDeadlineDetail').textContent = `${dueDate.value} ${dueTime.value}`;
    document.getElementById('summaryInstructions').textContent = description.value || 'No specific instructions provided';
    document.getElementById('summaryCitation').textContent = citationStyle.options[citationStyle.selectedIndex].text;
    document.getElementById('summarySpacing').textContent = lineSpacing.value || 'Double';
    document.getElementById('summaryReportType').textContent = reportType.value || 'None specified';
    document.getElementById('summarySources').textContent = sources.value || 0;
}

function calculateAndUpdatePrice() {
    const service = document.getElementById('service');
    const academicLevel = document.getElementById('academic_level');
    const wordCount = document.getElementById('word_count');
    const deadlineHours = document.getElementById('deadline_hours');
    const reportType = document.getElementById('report_type');

    // Validate required fields
    if (!service.value || !academicLevel.value || !wordCount.value || !deadlineHours.value) {
        return;
    }

    // Show loading state
    document.getElementById('summaryPricePerPage').textContent = 'Calculating...';
    document.getElementById('summaryPricePerPage').className = 'summary-value price-loading';
    document.getElementById('summaryReportPrice').textContent = 'Calculating...';
    document.getElementById('summaryReportPrice').className = 'summary-value price-loading';
    document.getElementById('summaryTotal').textContent = 'Calculating...';
    document.getElementById('summaryTotal').className = 'summary-value price-loading';

    // Prepare data for API
    const priceData = {
        service_id: parseInt(service.value),
        academic_level_id: parseInt(academicLevel.value),
        deadline_data: parseFloat(deadlineHours.value),
        word_count: parseInt(wordCount.value),
        report_type: reportType.value || '', // Default report type
    };

    // Call the pricing API
    fetch(`${API_BASE_URL}/calculate-price`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.getElementById('csrfToken').value,
        },
        body: JSON.stringify(priceData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to calculate price');
        }
        return response.json();
    })
    .then(data => {
        // Store the price data
        currentPriceData = data;
        
        // Update the display
        document.getElementById('summaryPricePerPage').textContent = `$${data.price_per_page.toFixed(2)}`;
        document.getElementById('summaryPricePerPage').className = 'summary-value';
        document.getElementById('summaryReportPrice').textContent = `$${data.report_price.toFixed(2)}`;
        document.getElementById('summaryReportPrice').className = 'summary-value';
        document.getElementById('summaryTotal').textContent = `$${data.total_price.toFixed(2)}`;
        document.getElementById('summaryTotal').className = 'summary-value';
    })
    .catch(error => {
        console.error('Error calculating price:', error);
        document.getElementById('summaryPricePerPage').textContent = 'Error calculating price';
        document.getElementById('summaryPricePerPage').className = 'summary-value';
        document.getElementById('summaryReportPrice').textContent = 'Error calculating price';
        document.getElementById('summaryReportPrice').className = 'summary-value';
        document.getElementById('summaryTotal').textContent = 'Error calculating price';
        document.getElementById('summaryTotal').className = 'summary-value';
    });
}

function submitOrder() {
    // Validate that we have price data
    if (!currentPriceData) {
        alert('Please wait for price calculation to complete.');
        return;
    }

    // Collect all form data
    const formData = new FormData();
    
    // Add all form fields
    const fields = [
        'service', 'academic_level', 'title', 'word_count', 
        'citation_style', 'line_spacing', 'sources', 'description', 'report_type'
    ];
    
    fields.forEach(field => {
        const element = document.getElementById(field);
        if (element) {
            formData.append(field, element.value);
        }
    });

    // Add deadline hours
    const dueDate = document.getElementById('due_date').value;
    const dueTime = document.getElementById('due_time').value;
    const deadlineHours = document.getElementById('deadline_hours').value;

    
    const formattedDateTime = `${dueDate}, ${dueTime}`;
    
    formData.append('deadline', deadlineHours);
    formData.append('due_date', `${formattedDateTime}`);

    // Add files
    const fileInput = document.getElementById('fileInput');
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('files', fileInput.files[i]);
    }

    // Calculate additional fields
    const wordCount = parseInt(document.getElementById('word_count').value) || 275;
    const pages = Math.ceil(wordCount / 275) || 1;
    
    formData.append('pages', pages);
    formData.append('total_price', currentPriceData.total_price);
    formData.append('price_per_page', currentPriceData.price_per_page);
    
    // Add submit_later checkbox
    const submitLater = document.getElementById('submitLater');
    if (submitLater && submitLater.checked) {
        formData.append('submit_later', 'true');
    }

    // Show loading state
    const submitButton = document.querySelector('.btn-submit');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Processing...';
    submitButton.disabled = true;
    submitButton.classList.add('loading');

    // Submit the order
    fetch(`${API_BASE_URL}/orders/new`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
        headers: {
            'X-CSRFToken': document.getElementById('csrfToken').value,
        }
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
            return; // Stop further handling
        }

        if (!response.ok) {
            throw new Error('Failed to submit order');
        }

        return response.json();
    })
    .then(data => {
        if (!data) return; // Already redirected

        if (data.redirect_url) {
            window.location.href = data.redirect_url;
        } else if (data.order_id) {
            window.location.href = `/payment/checkout/${data.order_id}`;
        } else {
            alert('Order submitted successfully!');
            document.getElementById('orderForm').reset();
            currentStep = 1;
            document.getElementById('step3').classList.remove('active');
            document.getElementById('step1').classList.add('active');
            updateProgressBar();
        }
    })
    .catch(error => {
        console.error('Error submitting order:', error);
        alert('There was an error submitting your order. Please try again.');
    })
    .finally(() => {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
        submitButton.classList.remove('loading');
    });
}


function goBack() {
    // Navigate back to previous page or home
    window.history.back();
}

function showOrderDetails() {
    // This function can be used to show order details if needed
    // Currently just for navigation styling
}

// Additional utility functions
function formatDeadline(dateStr, timeStr) {
    const date = new Date(`${dateStr}T${timeStr}`);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function validateFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const maxFileSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ];

    for (let i = 0; i < fileInput.files.length; i++) {
        const file = fileInput.files[i];
        
        if (file.size > maxFileSize) {
            alert(`File "${file.name}" is too large. Maximum file size is 10MB.`);
            return false;
        }
        
        if (!allowedTypes.includes(file.type)) {
            alert(`File "${file.name}" is not a supported format.`);
            return false;
        }
    }
    
    return true;
}

// Enhanced form validation
function validateStep1() {
    const service = document.getElementById('service');
    const academicLevel = document.getElementById('academic_level');
    const dueDate = document.getElementById('due_date');
    const dueTime = document.getElementById('due_time');

    if (!service.value) {
        alert('Please select a service type.');
        service.focus();
        return false;
    }

    if (!academicLevel.value) {
        alert('Please select a project level.');
        academicLevel.focus();
        return false;
    }

    if (!dueDate.value) {
        alert('Please select a due date.');
        dueDate.focus();
        return false;
    }

    if (!dueTime.value) {
        alert('Please select a due time.');
        dueTime.focus();
        return false;
    }

    updateDeadlineHours();
    const deadlineHours = parseFloat(document.getElementById('deadline_hours').value);
    if (deadlineHours <= 0) {
        alert('Deadline must be in the future.');
        dueDate.focus();
        return false;
    }

    return true;
}

function validateStep2() {
    const title = document.getElementById('title');
    const wordCount = document.getElementById('word_count');

    if (!title.value.trim()) {
        alert('Please enter a paper title.');
        title.focus();
        return false;
    }

    if (!wordCount.value || parseInt(wordCount.value) <= 0) {
        alert('Please enter a valid word count.');
        wordCount.focus();
        return false;
    }

    // Validate file upload if files are selected
    if (document.getElementById('fileInput').files.length > 0) {
        if (!validateFileUpload()) {
            return false;
        }
    }

    return true;
}

// Override the existing validateCurrentStep function
function validateCurrentStep() {
    switch (currentStep) {
        case 1:
            return validateStep1();
        case 2:
            return validateStep2();
        case 3:
            return true; 
        default:
            return true;
    }
}

// Add drag and drop functionality for file upload
function setupDragAndDrop() {
    const fileUpload = document.querySelector('.file-upload');
    
    fileUpload.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#4a7c59';
        this.style.backgroundColor = '#f0f8f0';
    });

    fileUpload.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#ddd';
        this.style.backgroundColor = '#fafafa';
    });

    fileUpload.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '#ddd';
        this.style.backgroundColor = '#fafafa';
        
        const files = e.dataTransfer.files;
        const fileInput = document.getElementById('fileInput');
        fileInput.files = files;
        
        // Trigger the change event
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
    });
}

// Initialize drag and drop when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
});