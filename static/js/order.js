document.addEventListener('DOMContentLoaded', function() {
    // Order form functionality
    const orderForm = document.getElementById('order-form');
    const orderTypeRadios = document.querySelectorAll('input[name="order_type"]');
    const addressSelectContainer = document.getElementById('address-select-container');
    const addressSelect = document.getElementById('address_id');
    
    if (orderForm && orderTypeRadios.length > 0) {
        // Toggle address selection based on order type
        orderTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'delivery' && addressSelectContainer) {
                    addressSelectContainer.classList.remove('d-none');
                    if (addressSelect) {
                        addressSelect.setAttribute('required', 'required');
                    }
                } else if (addressSelectContainer) {
                    addressSelectContainer.classList.add('d-none');
                    if (addressSelect) {
                        addressSelect.removeAttribute('required');
                    }
                }
            });
        });
        
        // Validate order form before submission
        orderForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Get cart from localStorage
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            
            if (cart.length === 0) {
                alert('Your cart is empty. Please add items before placing an order.');
                return;
            }
            
            // Check if delivery selected but no address
            const orderType = document.querySelector('input[name="order_type"]:checked').value;
            
            if (orderType === 'delivery' && addressSelect && addressSelect.value === '0') {
                alert('Please select a delivery address or add a new one.');
                addressSelect.focus();
                return;
            }
            
            // Submit the form
            this.submit();
        });
    }
    
    // Payment method selection
    const paymentMethodRadios = document.querySelectorAll('input[name="payment_method"]');
    const upiSection = document.getElementById('upi-payment-section');
    
    if (paymentMethodRadios.length > 0 && upiSection) {
        paymentMethodRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'upi') {
                    upiSection.classList.remove('d-none');
                } else {
                    upiSection.classList.add('d-none');
                }
            });
        });
    }
    
    // UPI payment confirmation
    const upiConfirmBtn = document.getElementById('upi-confirm-btn');
    const paymentStatusField = document.getElementById('payment_status');
    
    if (upiConfirmBtn && paymentStatusField) {
        upiConfirmBtn.addEventListener('click', function() {
            // Update payment status field (simulation only)
            paymentStatusField.value = 'completed';
            
            // Show confirmation message
            alert('Payment confirmed! Your order will be processed shortly.');
            
            // Disable this button to prevent multiple clicks
            this.disabled = true;
            this.textContent = 'Payment Confirmed';
            this.classList.remove('btn-primary');
            this.classList.add('btn-success');
        });
    }
    
    // Order tracking functionality
    const trackOrderForm = document.getElementById('track-order-form');
    
    if (trackOrderForm) {
        trackOrderForm.addEventListener('submit', function(event) {
            // Form is submitted directly to server, no need to prevent default
        });
    }
});
