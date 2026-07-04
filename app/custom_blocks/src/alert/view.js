/**
 * AEO Alert Status — Frontend View Script
 *
 * Handles the click dismiss event on dismissible status banners.
 */
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.aeo-alert-banner');

    alerts.forEach((alert) => {
        const closeBtn = alert.querySelector('.alert-close');
        if (!closeBtn) return;

        closeBtn.addEventListener('click', () => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(10px)';

            // Remove from layout after transition completes
            setTimeout(() => {
                alert.remove();
            }, 400);
        });
    });
});
