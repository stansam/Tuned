function payNow(orderId) {
    window.location.href = `/checkout/${orderId}`;
}

function approveDelivery(deliveryId) {
    if (confirm('Are you sure you want to approve this delivery?')) {
        fetch(`${API_BASE_URL}/client/order/${orderId}/complete`, {
            method: 'POST',
            credentials: include,
            headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.getElementById('csrfTokenMeta').getAttribute('content')
                },
            body: JSON.stringify({
                delivery_id: deliveryId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Delivery approved successfully!');
                location.reload();
            } else {
                alert('Error approving delivery: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error approving delivery. Please try again.');
        });
    }
}

function requestRevision(deliveryId) {
    const reason = prompt('Please provide a reason for the revision request:');
    if (reason && reason.trim() !== '') {
        fetch(`${API_BASE_URL}/client/order/${orderId}/revision`, {
            method: 'POST',
            headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.getElementById('csrfTokenMeta').getAttribute('content')
                },
            body: JSON.stringify({
                // delivery_id: deliveryId,
                revision_details: reason
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Revision request submitted successfully!');
                location.reload();
            } else {
                alert('Error requesting revision: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error requesting revision. Please try again.');
        });
    }
}

// Quick actions
function downloadFiles(url) {
    window.location.href = url;
}

function contactSupport() {
    window.location.href = '/client/support';
}