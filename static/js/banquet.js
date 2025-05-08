document.addEventListener('DOMContentLoaded', function() {
    const banquetForm = document.getElementById('banquet-form');
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const guestsInput = document.getElementById('guests');
    
    if (banquetForm && dateInput) {
        // Set min date to today
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        dateInput.setAttribute('min', formattedDate);
        
        // Handle form submission
        banquetForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Validate form inputs
            if (!validateBanquetForm()) {
                return;
            }
            
            // Submit the form
            this.submit();
        });
        
        // Function to validate banquet form
        function validateBanquetForm() {
            let isValid = true;
            
            // Required fields
            const requiredFields = ['name', 'email', 'phone', 'event_type', 'date', 'time', 'guests'];
            
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
            if (guestsInput.value.trim()) {
                const guestsCount = parseInt(guestsInput.value);
                
                if (guestsCount < 25) {
                    isValid = false;
                    guestsInput.classList.add('is-invalid');
                    document.getElementById('guests-feedback').textContent = 'Banquet bookings require a minimum of 25 guests.';
                } else if (guestsCount > 200) {
                    isValid = false;
                    guestsInput.classList.add('is-invalid');
                    document.getElementById('guests-feedback').textContent = 'Maximum capacity is 200 guests. Please contact us for larger events.';
                }
            }
            
            return isValid;
        }
        
        // Add input event listeners for form validation
        banquetForm.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid');
            });
        });
        
        // Handle event type change to show different form fields
        const eventTypeSelect = document.getElementById('event_type');
        const specialRequirementsSection = document.getElementById('special-requirements-section');
        
        if (eventTypeSelect && specialRequirementsSection) {
            eventTypeSelect.addEventListener('change', function() {
                const selectedType = this.value;
                
                // Show different placeholder text based on event type
                const requirementsTextarea = document.getElementById('requirements');
                
                if (requirementsTextarea) {
                    switch (selectedType) {
                        case 'wedding':
                            requirementsTextarea.placeholder = 'Please let us know any specific arrangements for the wedding reception, such as decoration theme, special menu requests, etc.';
                            break;
                        case 'birthday':
                            requirementsTextarea.placeholder = 'Let us know any special arrangements for the birthday celebration, such as cake, decorations, etc.';
                            break;
                        case 'corporate':
                            requirementsTextarea.placeholder = 'Please specify any requirements for the corporate event, such as audio-visual equipment, seating arrangement, etc.';
                            break;
                        default:
                            requirementsTextarea.placeholder = 'Please specify any special requirements for your event';
                    }
                }
            });
        }
    }
    
    // Gallery carousel functionality
    const galleryCarousel = document.getElementById('banquet-gallery-carousel');
    
    if (galleryCarousel) {
        const carouselInstance = new bootstrap.Carousel(galleryCarousel, {
            interval: 3000,
            wrap: true
        });
    }
});
