/**
 * AEO Form Builder — Frontend View Script
 *
 * Handles:
 * 1. Form validation and submit prevention
 * 2. Visual loading spinner state on the submit button
 * 3. Dynamic glassmorphic success/error feedback banner injection
 */
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('.aeo-form');

    forms.forEach((form) => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            // ── Form Validation ──────────────────────────────────
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            const submitBtn = form.querySelector('.aeo-form-submit-btn');
            if (!submitBtn) return;

            // ── Loading Spinner State ────────────────────────────
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;

            // Disable all input fields during submission
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => input.disabled = true);

            // Remove any existing feedback alert banners
            const existingAlert = form.querySelector('.aeo-form-alert');
            if (existingAlert) {
                existingAlert.remove();
            }

            // ── Mock Submission (1.5 seconds) ────────────────────
            setTimeout(() => {
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
                inputs.forEach(input => input.disabled = false);

                // Create a beautiful, glassmorphic success feedback banner
                const alertBanner = document.createElement('div');
                alertBanner.className = 'aeo-form-alert success-alert';
                alertBanner.role = 'alert';
                alertBanner.innerHTML = `
                    <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <span class="alert-message">Submission successful! Thank you for your interest.</span>
                `;

                // Inject right before the submit button wrapper
                const submitWrap = form.querySelector('.form-submit-wrap');
                form.insertBefore(alertBanner, submitWrap);

                // Reset the form values
                form.reset();

                // Auto-fadeout the alert banner after 60 seconds (better accessibility)
                setTimeout(() => {
                    alertBanner.style.opacity = '0';
                    alertBanner.style.transform = 'translateY(8px)';
                    setTimeout(() => alertBanner.remove(), 400);
                }, 60000);

            }, 1500);
        });
    });
});
