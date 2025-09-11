let currentStep = 1;
const totalSteps = 3;
let currentPriceData = null;

// Initialize instances
let serviceChoices = null;
let academicLevelChoices = null;
let datePicker = null;
let timePicker = null;

// Initialize form
document.addEventListener('DOMContentLoaded', function() {
    initializeCustomSelects();
    initializeDateTimePickers();
    initializeTemplateVariables();
    updateProgressBar();
    setupEventListeners();
});

async function initializeCustomSelects() {
    try {
        // Initialize service select with categories
        await initializeServiceSelect();
        
        // Initialize academic level select
        await initializeAcademicLevelSelect();
        
    } catch (error) {
        console.error('Error initializing custom selects:', error);
        // Fallback to default selects if API fails
        initializeFallbackSelects();
    }
}

async function initializeServiceSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/client/new-order/services-with-categories`, {
            credentials: 'include',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch services');
        
        const categories = await response.json();
        const serviceSelect = document.getElementById('service');
        
        // Clear existing options
        serviceSelect.innerHTML = '';
        
        // Populate with grouped options
        categories.forEach(category => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = category.name;
            
            category.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service.id;
                option.textContent = service.name;
                optgroup.appendChild(option);
            });
            
            serviceSelect.appendChild(optgroup);
        });
        
        // Initialize Choices.js
        serviceChoices = new Choices(serviceSelect, {
            searchEnabled: true,
            itemSelectText: '',
            noChoicesText: 'No services available',
            noResultsText: 'No services found',
            placeholder: true,
            placeholderValue: 'Select Service',
            classNames: {
                containerInner: 'choices__inner--service'
            }
        });
        
    } catch (error) {
        console.error('Error initializing service select:', error);
        throw error;
    }
}

async function initializeAcademicLevelSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/client/new-order/project-level`, {
            credentials: 'include',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) throw new Error('Failed to fetch academic levels');
        
        const levels = await response.json();
        const levelSelect = document.getElementById('academic_level');
        
        // Clear existing options
        levelSelect.innerHTML = '';
        
        // Populate options
        levels.forEach(level => {
            const option = document.createElement('option');
            option.value = level.id;
            option.textContent = level.name;
            levelSelect.appendChild(option);
        });
        
        // Initialize Choices.js
        academicLevelChoices = new Choices(levelSelect, {
            searchEnabled: false,
            itemSelectText: '',
            noChoicesText: 'No levels available',
            placeholder: true,
            placeholderValue: 'Select Level',
            classNames: {
                containerInner: 'choices__inner--level'
            }
        });
        
    } catch (error) {
        console.error('Error initializing academic level select:', error);
        throw error;
    }
}

function initializeFallbackSelects() {
    console.warn('Using fallback initialization for selects');
    // Keep existing HTML structure as fallback
}

function initializeDateTimePickers() {
    // Date picker
    datePicker = flatpickr("#due_date", {
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "j M, Y",
        minDate: "today",
        maxDate: new Date().fp_incr(30),
        defaultDate: new Date(),
        locale: {
            firstDayOfWeek: 1 
        },
        onChange: function(selectedDates, dateStr, instance) {
            adjustTimeMin(selectedDates[0]);
            updateDeadlineHours();
            if (currentStep === 3) {
                calculateAndUpdatePrice();
            }
        }
    });
    
    // Time picker
    const minTimeObj = new Date(Date.now() + 3 * 60 * 60 * 1000);
    timePicker = flatpickr("#due_time", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: false,
        defaultDate: minTimeObj,
        minTime: minTimeObj.toTimeString().slice(0,5),
        onChange: function(selectedDates, timeStr, instance) {
            updateDeadlineHours();
            if (currentStep === 3) {
                calculateAndUpdatePrice();
            }
        }
    });
}

function adjustTimeMin(selectedDate) {
    const now = new Date();
    const minTimeObj = new Date(Date.now() + 3 * 60 * 60 * 1000);
    const minTimeStr = minTimeObj.toTimeString().slice(0,5);

    const isToday = selectedDate.toDateString() === now.toDateString();

    if (isToday) {
        timePicker.set("minTime", minTimeStr);

        const currentTime = timePicker.selectedDates[0];
        if (!currentTime || currentTime < minTimeObj) {
            timePicker.setDate(minTimeObj, true);
        }
    } else {
        timePicker.set("minTime", "00:00");
    }
}

function initializeTemplateVariables() {
    // Check if template variables exist
    if (typeof window.TEMPLATE_VARS === 'undefined') {
        console.log('No template variables found');
        return;
    }
    
    const vars = window.TEMPLATE_VARS;
    
    // Set service if provided
    if (vars.selected_service && serviceChoices) {
        setTimeout(() => {
            serviceChoices.setChoiceByValue(vars.selected_service.id.toString());
        }, 100); // Small delay to ensure Choices.js is ready
    }
    
    // Set academic level if provided
    if (vars.selected_academic_level && academicLevelChoices) {
        setTimeout(() => {
            academicLevelChoices.setChoiceByValue(vars.selected_academic_level.id.toString());
        }, 100);
    }
    
    // Set word count if provided
    if (vars.word_count) {
        const wordCountField = document.getElementById('word_count');
        if (wordCountField) {
            wordCountField.value = vars.word_count;
            // Trigger input event to update page count
            wordCountField.dispatchEvent(new Event('input'));
        }
    }
    
    // Set due date if provided
    if (vars.due_date && datePicker) {
        try {
            const date = new Date(vars.due_date);
            if (!isNaN(date.getTime())) {
                datePicker.setDate(date);
            }
        } catch (error) {
            console.warn('Invalid due_date format:', vars.due_date);
        }
    }
    
    // Set deadline hours if provided
    if (vars.hoursUntilDeadline) {
        const deadlineField = document.getElementById('deadline_hours');
        if (deadlineField) {
            deadlineField.value = vars.hoursUntilDeadline;
        }
    }
    
    console.log('Template variables initialized:', vars);
}

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

    // Report Type toggle
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
    // These will be triggered by Choices.js change events
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

            displayInfo.classList.add('file-display');
            fileUpload.appendChild(displayInfo);
        }
    });

    // Setup drag and drop
    setupDragAndDrop();
}

function updateDeadlineHours() {
    const dateInput = document.getElementById('due_date');
    const timeInput = document.getElementById('due_time');
    const deadlineField = document.getElementById('deadline_hours');
    
    const dateValue = dateInput.value;
    const timeValue = timeInput.value;
    
    if (dateValue && timeValue) {
        const deadlineDateTime = new Date(`${dateValue}T${timeValue}`);
        const now = new Date();
        const hoursUntilDeadline = (deadlineDateTime - now) / (1000 * 60 * 60);
        
        deadlineField.value = Math.max(0, hoursUntilDeadline);
        
        // Recalculate price if we're on the summary step
        if (currentStep === 3) {
            calculateAndUpdatePrice();
        }
    }
}

// Rest of your existing functions remain the same...
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
            // For Choices.js selects, highlight the container instead
            if (field.classList.contains('choices__input')) {
                const choicesContainer = field.closest('.choices');
                if (choicesContainer) {
                    choicesContainer.classList.add('is-invalid');
                }
            } else {
                field.style.borderColor = '#dc3545';
            }
            isValid = false;
        } else {
            // Remove error styling
            if (field.classList.contains('choices__input')) {
                const choicesContainer = field.closest('.choices');
                if (choicesContainer) {
                    choicesContainer.classList.remove('is-invalid');
                }
            } else {
                field.style.borderColor = '#ddd';
            }
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
    // Get form values - accounting for Choices.js
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

    // Get text from Choices.js selections
    const serviceText = serviceChoices ? 
        serviceChoices.getValue(true) : 
        (service.options[service.selectedIndex] ? service.options[service.selectedIndex].text : '-');
        
    const levelText = academicLevelChoices ? 
        academicLevelChoices.getValue(true) : 
        (academicLevel.options[academicLevel.selectedIndex] ? academicLevel.options[academicLevel.selectedIndex].text : '-');

    // Update summary display
    document.getElementById('summaryService').textContent = serviceText;
    document.getElementById('summaryServiceType').textContent = serviceText;
    document.getElementById('summaryLevel').textContent = levelText;
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
        report_type: reportType.value || '',
    };

    // Call the pricing API
    fetch(`${API_BASE_URL}/calculate-price`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            "X-Requested-With": "XMLHttpRequest",
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
    const orderFormUrl = document.getElementById('orderForm').action;
    fetch(orderFormUrl, {
        method: 'POST',
        credentials: 'include',
        body: formData,
        headers: {
            "X-Requested-With": "XMLHttpRequest",
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
        if (serviceChoices) {
            serviceChoices.showDropdown();
        }
        service.focus();
        return false;
    }

    if (!academicLevel.value) {
        alert('Please select a project level.');
        if (academicLevelChoices) {
            academicLevelChoices.showDropdown();
        }
        academicLevel.focus();
        return false;
    }

    if (!dueDate.value) {
        alert('Please select a due date.');
        if (datePicker) {
            datePicker.open();
        }
        dueDate.focus();
        return false;
    }

    if (!dueTime.value) {
        alert('Please select a due time.');
        if (timePicker) {
            timePicker.open();
        }
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
    
    if (!fileUpload) return;
    
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

// Cleanup function for when page is unloaded
window.addEventListener('beforeunload', function() {
    if (serviceChoices) {
        serviceChoices.destroy();
    }
    if (academicLevelChoices) {
        academicLevelChoices.destroy();
    }
    if (datePicker) {
        datePicker.destroy();
    }
    if (timePicker) {
        timePicker.destroy();
    }
});