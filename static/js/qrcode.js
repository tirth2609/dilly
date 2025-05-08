// Helper function to format currency
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}

document.addEventListener('DOMContentLoaded', function() {
    const qrContainer = document.getElementById('qr-code-container');
    const tableIdElement = document.getElementById('table-id');
    
    if (qrContainer && tableIdElement) {
        const tableId = tableIdElement.textContent.trim();
        
        // Generate QR code for the table
        fetch(`/api/generate-table-qr?table=${tableId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const qrImage = document.createElement('img');
                qrImage.src = data.qr_data;
                qrImage.alt = `Table ${tableId} QR Code`;
                qrImage.classList.add('img-fluid', 'qr-code-img');
                
                qrContainer.innerHTML = '';
                qrContainer.appendChild(qrImage);
            } else {
                console.error('Error generating QR code:', data.error);
            }
        })
        .catch(error => {
            console.error('Error generating QR code:', error);
        });
    }
    
    // QR Menu functionality
    const menuItems = document.querySelectorAll('.menu-item');
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');
    const placeOrderBtn = document.getElementById('place-order-btn');
    const orderForm = document.getElementById('qr-order-form');
    const tableInput = document.getElementById('table-input');
    
    // Initialize cart
    let cart = [];
    
    // Add event listeners to "Add to Cart" buttons
    function initializeAddToCartButtons() {
        document.querySelectorAll('.add-to-cart-btn').forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                const itemName = this.getAttribute('data-item-name');
                const itemPrice = parseFloat(this.getAttribute('data-item-price'));
                
                addToQrCart(itemId, itemName, itemPrice);
            });
        });
    }
    
    // Initialize buttons
    initializeAddToCartButtons();
    
    // Function to add item to QR cart
    function addToQrCart(id, name, price, quantity = 1) {
        // Check if item already in cart
        const existingItemIndex = cart.findIndex(item => item.id === id);
        
        if (existingItemIndex !== -1) {
            // Update quantity
            cart[existingItemIndex].quantity += quantity;
        } else {
            // Add new item
            cart.push({
                id: id,
                name: name,
                price: price,
                quantity: quantity
            });
        }
        
        // Update cart UI
        updateQrCartUI();
    }
    
    // Function to update QR cart UI
    function updateQrCartUI() {
        if (!cartItems || !cartTotal) return;
        
        // Clear current items
        cartItems.innerHTML = '';
        
        if (cart.length === 0) {
            cartItems.innerHTML = '<p class="text-center">Your cart is empty</p>';
            if (placeOrderBtn) {
                placeOrderBtn.disabled = true;
            }
        } else {
            let total = 0;
            
            // Add each item to cart
            cart.forEach((item, index) => {
                const itemTotal = item.price * item.quantity;
                total += itemTotal;
                
                const cartItemHtml = `
                <div class="cart-item">
                    <div class="d-flex justify-content-between">
                        <span>${item.name}</span>
                        <span>${formatCurrency(item.price)}</span>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <div class="input-group input-group-sm" style="max-width: 120px;">
                            <button class="btn btn-outline-secondary cart-qty-btn" data-action="decrease" data-index="${index}">-</button>
                            <input type="number" class="form-control text-center" value="${item.quantity}" min="1" data-index="${index}">
                            <button class="btn btn-outline-secondary cart-qty-btn" data-action="increase" data-index="${index}">+</button>
                        </div>
                        <span>${formatCurrency(itemTotal)}</span>
                    </div>
                    <div class="text-end mt-2">
                        <button class="btn btn-sm btn-outline-danger cart-remove-btn" data-index="${index}">Remove</button>
                    </div>
                </div>
                <hr>
                `;
                
                cartItems.innerHTML += cartItemHtml;
            });
            
            // Update total
            cartTotal.textContent = formatCurrency(total);
            
            if (placeOrderBtn) {
                placeOrderBtn.disabled = false;
            }
            
            // Add event listeners for cart controls
            attachQrCartListeners();
        }
    }
    
    // Function to attach event listeners to QR cart controls
    function attachQrCartListeners() {
        // Quantity buttons
        document.querySelectorAll('.cart-qty-btn').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                const action = this.getAttribute('data-action');
                
                if (action === 'increase') {
                    cart[index].quantity += 1;
                } else if (action === 'decrease') {
                    if (cart[index].quantity > 1) {
                        cart[index].quantity -= 1;
                    }
                }
                
                updateQrCartUI();
            });
        });
        
        // Quantity inputs
        document.querySelectorAll('.cart-item input[type="number"]').forEach(input => {
            input.addEventListener('change', function() {
                const index = parseInt(this.getAttribute('data-index'));
                let quantity = parseInt(this.value);
                
                if (isNaN(quantity) || quantity < 1) {
                    quantity = 1;
                    this.value = 1;
                }
                
                cart[index].quantity = quantity;
                updateQrCartUI();
            });
        });
        
        // Remove buttons
        document.querySelectorAll('.cart-remove-btn').forEach(button => {
            button.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                cart.splice(index, 1);
                updateQrCartUI();
            });
        });
    }
    
    // Handle QR order form submission
    if (orderForm) {
        orderForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            if (cart.length === 0) {
                alert('Your cart is empty. Please add items before placing an order.');
                return;
            }
            
            // Get form data
            const formData = new FormData(orderForm);
            const customerData = {
                name: formData.get('customer_name') || 'Table Customer',
                email: formData.get('customer_email') || 'table@example.com',
                phone: formData.get('customer_phone') || '0000000000',
                special_instructions: formData.get('special_instructions') || '',
                table_id: formData.get('table_id'),
                items: cart
            };
            
            // Send order to server
            fetch('/qr-menu/order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(customerData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    const successMessage = document.getElementById('order-success-message');
                    const orderIdElement = document.getElementById('order-id');
                    
                    if (successMessage && orderIdElement) {
                        orderIdElement.textContent = data.order_id;
                        successMessage.classList.remove('d-none');
                        
                        // Hide order form
                        orderForm.classList.add('d-none');
                        
                        // Clear cart
                        cart = [];
                        updateQrCartUI();
                    }
                } else {
                    alert('Error placing order: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error placing order:', error);
                alert('Error placing order. Please try again.');
            });
        });
    }
    
    // Clear QR cart button
    const clearQrCartBtn = document.getElementById('clear-cart-btn');
    if (clearQrCartBtn) {
        clearQrCartBtn.addEventListener('click', function() {
            cart = [];
            updateQrCartUI();
        });
    }
    
    // Initialize QR cart UI
    if (cartItems && cartTotal) {
        updateQrCartUI();
    }
});
