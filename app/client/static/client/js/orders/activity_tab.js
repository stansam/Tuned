document.getElementById('comment-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const content = document.getElementById('comment-content').value.trim();
    const orderId = document.getElementById('activityOrderId').value
    if (!content) return;
    
    fetch(`${API_BASE_URL}/client/order-activities/order/comment`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf_token"]').getAttribute('content')
        },
        body: JSON.stringify({
            order_id: orderId, 
            message: content
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Reload to show new comment
        } else {
            alert('Failed to add comment: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to add comment');
    });
});

// document.getElementById('highlight-file-option').addEventListener('click', function() {
//     const modal = new bootstrap.Modal(document.getElementById('highlightFileModal'));
//     modal.show();
//     document.getElementById('file-menu').classList.remove('show');
// });
// let selectedFile = null;
    
// document.querySelectorAll('.file-item').forEach(item => {
//     item.addEventListener('click', function(e) {
//         e.preventDefault();
//         document.querySelectorAll('.file-item').forEach(i => i.classList.remove('active'));
//         this.classList.add('active');
//         selectedFile = {
//             id: this.dataset.fileId,
//             name: this.dataset.fileName,
//             type: this.dataset.fileType
//         };
//     });
// });