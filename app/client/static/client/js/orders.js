function refreshOrders() {
    window.location.reload();
}

function updateSort(sortValue) {
    const url = new URL(window.location);
    url.searchParams.set('sort_by', sortValue);
    window.location.href = url.toString();
}

function handleSearch(event) {
    if (event.key === 'Enter') {
        const searchTerm = event.target.value;
        const url = new URL(window.location);
        if (searchTerm) {
            url.searchParams.set('search', searchTerm);
        } else {
            url.searchParams.delete('search');
        }
        window.location.href = url.toString();
    }
}

function showOrderActions(orderId) {
    // Handle order actions menu
    console.log('Show actions for order:', orderId);
    // You can implement a dropdown menu or modal here
}
