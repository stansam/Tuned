function switchTab(evt, tabName) {
    var i, tabcontent, tablinks;
    
    // Hide all tab contents
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove("active");
    }
    
    // Remove active class from all tab buttons
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }
    
    // Show the selected tab content and mark button as active
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

// Countdown timer functionality
function updateCountdown() {
    const dueDate = new Date(document.getElementById('countdown').dataset.deadline);
    const now = new Date();
    const distance = dueDate - now;
    // console.log("Due Date:", dueDate);
    // console.log("Distance:", distance);

    if (distance > 0) {
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        document.getElementById("days").textContent = days.toString().padStart(2, '0');
        document.getElementById("hours").textContent = hours.toString().padStart(2, '0');
        document.getElementById("minutes").textContent = minutes.toString().padStart(2, '0');
        document.getElementById("seconds").textContent = seconds.toString().padStart(2, '0');
    } else {
        // Timer expired
        document.getElementById("days").textContent = "00";
        document.getElementById("hours").textContent = "00";
        document.getElementById("minutes").textContent = "00";
        document.getElementById("seconds").textContent = "00";
    }
}

// Update countdown every second
setInterval(updateCountdown, 1000);

// Initialize countdown on page load
updateCountdown();

// Copy order number functionality
function copyOrderNumber() {
    const orderNumber = "{{ order.order_number }}";
    navigator.clipboard.writeText(orderNumber).then(function() {
        // You can add a toast notification here
        console.log('Order number copied to clipboard');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Wait for both socketClient and OrderChatHandler to be available
    const initChat = () => {
        if (typeof socketClient !== 'undefined' && typeof OrderChatHandler !== 'undefined') {
            const orderChatCardCont = document.getElementById('orderChatCard');
            if(orderChatCardCont){
                const orderId = orderChatCardCont.dataset.orderId;  // Template variable
                const chatId = orderChatCardCont.dataset.chatId;  // Template variable
                
                window.orderChatHandler = new OrderChatHandler(orderId, chatId);
            }
        } else {
            setTimeout(initChat, 100);
        }
    };
    
    initChat();
});

function goBack() {
    window.history.back();
}