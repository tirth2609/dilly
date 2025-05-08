document.addEventListener('DOMContentLoaded', function() {
    const reservationForm = document.getElementById('reservation-form');
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    
    if (reservationForm && dateInput && timeSelect) {
        // Set min date to today
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        dateInput.setAttribute('min', formattedDate);
        
        // When date changes, check available time slots
        dateInput.addEventListener('change', function() {
            const selectedDate = this.value;
            
            if (!selectedDate) return;
            
            // Get available time slots for the selected date
            fetch('/api/check-time-slots', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ date: selectedDate })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateTimeSlots(data.available_slots);
                } else {
                    console.error('Error checking time slots:', data.error);
                }
            })
            .catch(error => {
                console.error('Error checking time slots:', error);
            });
        });
        
        // Function to update time slots based on availability
        function updateTimeSlots(availableSlots) {
            // Clear current options
            timeSelect.innerHTML = '';
            
            // Add new options
            availableSlots.forEach(slot => {
                const option = document.createElement('option');
                option.value = slot.time;
                option.textContent = slot.label;
                option.disabled = !slot.available;
                
                if (!slot.available) {
                    option.textContent += ' (Not Available)';
                }
                
                timeSelect.appendChild(option);
            });
        }
        
        // Handle form submission
        reservationForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Validate form inputs
            if (!validateReservationForm()) {
                return;
            }
            
            // Submit the form
            this.submit();
        });
        
        // Function to validate reservation form
        function validateReservationForm() {
            let isValid = true;
            
            // Required fields
            const requiredFields = ['name', 'email', 'phone', 'date', 'time', 'guests'];
            
            requiredFields.forEach(field => {
                const input = document.getElementById(field);
                
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            // Email validation
            const emailInput = document.getElementById('email');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (emailInput.value.trim() && !emailRegex.test(emailInput.value.trim())) {
                isValid = false;
                emailInput.classList.add('is-invalid');
            }
            
            // Phone validation
            const phoneInput = document.getElementById('phone');
            const phoneRegex = /^\d{10,15}$/;
            
            if (phoneInput.value.trim() && !phoneRegex.test(phoneInput.value.trim().replace(/[\s-]/g, ''))) {
                isValid = false;
                phoneInput.classList.add('is-invalid');
            }
            
            // Guests validation
            const guestsInput = document.getElementById('guests');
            
            if (guestsInput.value.trim() && (parseInt(guestsInput.value) < 1 || parseInt(guestsInput.value) > 20)) {
                isValid = false;
                guestsInput.classList.add('is-invalid');
            }
            
            return isValid;
        }
        
        // Add input event listeners for form validation
        reservationForm.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
            });
        });
    }
});
