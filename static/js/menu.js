document.addEventListener('DOMContentLoaded', function() {
    // Menu filtering functionality
    const filterForm = document.getElementById('menu-filter-form');
    const menuItems = document.querySelectorAll('.menu-item');
    
    if (filterForm) {
        filterForm.addEventListener('change', function() {
            const formData = new FormData(filterForm);
            const filters = {
                is_vegan: formData.has('is_vegan'),
                is_gluten_free: formData.has('is_gluten_free'),
                is_jain: formData.has('is_jain'),
                category_id: formData.get('category_id') || null
            };
            
            // Send AJAX request to filter menu
            fetch('/api/menu/filter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filters: filters })
            })
            .then(response => response.json())
            .then(data => {
                updateMenuDisplay(data);
            })
            .catch(error => {
                console.error('Error filtering menu:', error);
            });
        });
    }
    
    // Function to update menu display after filtering
    function updateMenuDisplay(menuItems) {
        const menuContainer = document.getElementById('menu-items-container');
        
        if (!menuContainer) return;
        
        // Clear current menu items
        menuContainer.innerHTML = '';
        
        if (menuItems.length === 0) {
            menuContainer.innerHTML = '<div class="col-12 text-center py-5"><h3>No items match your filter criteria</h3></div>';
            return;
        }
        
        // Create and append new menu items
        menuItems.forEach(item => {
            const menuItemHtml = `
            <div class="col-md-6 col-lg-4">
                <div class="menu-card">
                    <img src="${item.image_url || 'https://via.placeholder.com/300x200?text=Vegetarian+Dish'}" alt="${item.name}" class="menu-card-img">
                    <div class="menu-card-body">
                        <h5 class="menu-card-title">${item.name}</h5>
                        <p class="menu-card-text">${item.description || 'No description available'}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <p class="menu-card-price">${formatCurrency(item.price)}</p>
                            <button class="btn btn-sm btn-outline-primary add-to-cart-btn" data-item-id="${item.id}">Add to Cart</button>
                        </div>
                        <div class="menu-dietary-tags">
                            ${item.is_vegan ? '<span class="menu-dietary-tag tag-vegan">Vegan</span>' : ''}
                            ${item.is_gluten_free ? '<span class="menu-dietary-tag tag-gluten-free">Gluten Free</span>' : ''}
                            ${item.is_jain ? '<span class="menu-dietary-tag tag-jain">Jain</span>' : ''}
                        </div>
                    </div>
                </div>
            </div>`;
            
            menuContainer.innerHTML += menuItemHtml;
        });
        
        // Reattach event listeners for add to cart buttons
        attachAddToCartListeners();
    }
    
    // Function to attach event listeners to add to cart buttons
    function attachAddToCartListeners() {
        const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
        
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                addToCart(itemId, 1);
            });
        });
    }
    
    // Initial call to attach listeners
    attachAddToCartListeners();
    
    // Function to add item to cart
    function addToCart(itemId, quantity, notes = '') {
        fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: parseInt(itemId),
                quantity: parseInt(quantity),
                notes: notes
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update cart UI
                updateCartUI(data.cart);
                
                // Show confirmation message
                const toast = new bootstrap.Toast(document.getElementById('cart-toast'));
                document.getElementById('cart-toast-body').textContent = data.message;
                toast.show();
            } else {
                console.error('Error adding to cart:', data.error);
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
        });
    }
    
    // Function to update cart UI
    function updateCartUI(cart) {
        const cartItemsContainer = document.getElementById('cart-items');
        const cartTotalElement = document.getElementById('cart-total');
        const cartCountElement = document.getElementById('cart-count');
        
        if (!cartItemsContainer) return;
        
        // Clear current cart items
        cartItemsContainer.innerHTML = '';
        
        // Calculate total
        let total = 0;
        
        // Add cart items
        if (cart.length === 0) {
            cartItemsContainer.innerHTML = '<div class="text-center py-3">Your cart is empty</div>';
        } else {
            cart.forEach(item => {
                const itemTotal = item.price * item.quantity;
                total += itemTotal;
                
                const cartItemHtml = `
                <div class="cart-item">
                    <div class="d-flex justify-content-between">
                        <div class="cart-item-name">${item.name}</div>
                        <div class="cart-item-price">${formatCurrency(item.price)}</div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <div class="cart-item-quantity">
                            <div class="input-group input-group-sm">
                                <button class="btn btn-outline-secondary cart-quantity-btn" data-action="decrease" data-item-id="${item.id}">-</button>
                                <input type="number" class="form-control text-center cart-quantity-input" value="${item.quantity}" min="1" data-item-id="${item.id}">
                                <button class="btn btn-outline-secondary cart-quantity-btn" data-action="increase" data-item-id="${item.id}">+</button>
                            </div>
                        </div>
                        <div class="cart-item-subtotal">${formatCurrency(itemTotal)}</div>
                    </div>
                    <div class="text-end mt-2">
                        <button class="btn btn-sm btn-outline-danger cart-remove-btn" data-item-id="${item.id}">Remove</button>
                    </div>
                </div>`;
                
                cartItemsContainer.innerHTML += cartItemHtml;
            });
        }
        
        // Update total
        if (cartTotalElement) {
            cartTotalElement.textContent = formatCurrency(total);
        }
        
        // Update cart count
        if (cartCountElement) {
            const itemCount = cart.reduce((acc, item) => acc + item.quantity, 0);
            cartCountElement.textContent = itemCount;
            
            if (itemCount > 0) {
                cartCountElement.style.display = 'inline-block';
            } else {
                cartCountElement.style.display = 'none';
            }
        }
        
        // Attach event listeners to cart item elements
        attachCartItemListeners();
    }
    
    // Function to attach event listeners to cart item elements
    function attachCartItemListeners() {
        // Quantity change buttons
        document.querySelectorAll('.cart-quantity-btn').forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                const action = this.getAttribute('data-action');
                const inputElement = document.querySelector(`.cart-quantity-input[data-item-id="${itemId}"]`);
                let quantity = parseInt(inputElement.value);
                
                if (action === 'increase') {
                    quantity += 1;
                } else if (action === 'decrease') {
                    quantity = Math.max(1, quantity - 1);
                }
                
                inputElement.value = quantity;
                updateCartItem(itemId, quantity);
            });
        });
        
        // Quantity input fields
        document.querySelectorAll('.cart-quantity-input').forEach(input => {
            input.addEventListener('change', function() {
                const itemId = this.getAttribute('data-item-id');
                const quantity = parseInt(this.value);
                
                if (quantity < 1) {
                    this.value = 1;
                    updateCartItem(itemId, 1);
                } else {
                    updateCartItem(itemId, quantity);
                }
            });
        });
        
        // Remove buttons
        document.querySelectorAll('.cart-remove-btn').forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                removeFromCart(itemId);
            });
        });
    }
    
    // Function to update cart item quantity
    function updateCartItem(itemId, quantity) {
        fetch('/api/cart/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: parseInt(itemId),
                quantity: parseInt(quantity)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartUI(data.cart);
            } else {
                console.error('Error updating cart:', data.error);
            }
        })
        .catch(error => {
            console.error('Error updating cart:', error);
        });
    }
    
    // Function to remove item from cart
    function removeFromCart(itemId) {
        fetch('/api/cart/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: parseInt(itemId)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartUI(data.cart);
                
                const toast = new bootstrap.Toast(document.getElementById('cart-toast'));
                document.getElementById('cart-toast-body').textContent = data.message;
                toast.show();
            } else {
                console.error('Error removing from cart:', data.error);
            }
        })
        .catch(error => {
            console.error('Error removing from cart:', error);
        });
    }
    
    // Function to clear cart
    function clearCart() {
        fetch('/api/cart/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartUI([]);
                
                const toast = new bootstrap.Toast(document.getElementById('cart-toast'));
                document.getElementById('cart-toast-body').textContent = data.message;
                toast.show();
            } else {
                console.error('Error clearing cart:', data.error);
            }
        })
        .catch(error => {
            console.error('Error clearing cart:', error);
        });
    }
    
    // Clear cart button
    const clearCartButton = document.getElementById('clear-cart-btn');
    if (clearCartButton) {
        clearCartButton.addEventListener('click', clearCart);
    }
    
    // Load cart on page load
    function loadCart() {
        fetch('/api/cart')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartUI(data.cart);
            } else {
                console.error('Error loading cart:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading cart:', error);
        });
    }
    
    // Initial cart load
    loadCart();
});
