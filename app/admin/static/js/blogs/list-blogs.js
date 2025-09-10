document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2
    $('.category-select').select2({
        placeholder: "Select Category",
        allowClear: true,
        theme: "classic"
    });
    
    // View toggle functionality
    const listViewBtn = document.getElementById('listViewBtn');
    const gridViewBtn = document.getElementById('gridViewBtn');
    const listView = document.querySelector('.list-view');
    const gridView = document.querySelector('.grid-view');
    
    listViewBtn.addEventListener('click', function() {
        listViewBtn.classList.add('active');
        gridViewBtn.classList.remove('active');
        listView.classList.add('active');
        gridView.classList.remove('active');
        
        // Save preference to local storage
        localStorage.setItem('blogViewPreference', 'list');
    });
    
    gridViewBtn.addEventListener('click', function() {
        gridViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
        gridView.classList.add('active');
        listView.classList.remove('active');
        
        // Save preference to local storage
        localStorage.setItem('blogViewPreference', 'grid');
    });
    
    // Load view preference from local storage
    const savedView = localStorage.getItem('blogViewPreference');
    if (savedView === 'grid') {
        gridViewBtn.click();
    }
    
    // Handle delete post buttons
    const deleteButtons = document.querySelectorAll('.delete-post-btn');
    const deletePostForm = document.getElementById('deletePostForm');
    const postTitleToDelete = document.getElementById('postTitleToDelete');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.getAttribute('data-post-id');
            const postTitle = this.getAttribute('data-post-title');
            
            postTitleToDelete.textContent = postTitle;
            deletePostForm.action = `/admin/blog/${postId}/delete`;
            
            const deleteModal = new bootstrap.Modal(document.getElementById('deletePostModal'));
            deleteModal.show();
        });
    });
    
    // Add visual indicator to current sort option
    const sortLinks = document.querySelectorAll('.dropdown-item');
    sortLinks.forEach(link => {
        if (link.classList.contains('active')) {
            const sortText = link.textContent.trim().split('\n')[0];
            document.getElementById('sortDropdown').innerHTML = `<i class="fas fa-sort me-1"></i> ${sortText}`;
        }
    });
});