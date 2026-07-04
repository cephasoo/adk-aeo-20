document.addEventListener('DOMContentLoaded', () => {
    // Attach listener to all expandable quote toggle buttons
    const attachExpandListeners = () => {
        const toggleButtons = document.querySelectorAll('.wp-block-aeo-media-showcase .expand-toggle-btn');

        toggleButtons.forEach(btn => {
            if (btn.dataset.listenerAttached) return;
            btn.dataset.listenerAttached = 'true';

            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const card = btn.closest('.aeo-showcase-card');
                if (card) {
                    const isExpanded = card.classList.toggle('expanded');

                    // Update button text and state
                    const textSpan = btn.querySelector('.btn-text');
                    if (textSpan) {
                        textSpan.textContent = isExpanded ? 'Read Less' : 'Read Full Story';
                    }
                }
            });
        });
    };

    // Initialize all sliders/carousels
    const initSliders = () => {
        const showcases = document.querySelectorAll('.wp-block-aeo-media-showcase');
        showcases.forEach(showcase => {
            if (showcase.dataset.sliderInitialized) return;
            showcase.dataset.sliderInitialized = 'true';

            const grid = showcase.querySelector('.aeo-showcase-grid');
            const prevBtn = showcase.querySelector('.prev-btn');
            const nextBtn = showcase.querySelector('.next-btn');

            if (grid && prevBtn && nextBtn) {
                const getScrollAmount = () => {
                    const card = grid.querySelector('.aeo-showcase-card');
                    return card ? card.offsetWidth + 24 : grid.offsetWidth; // card width + gap
                };

                prevBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    grid.scrollBy({ left: -getScrollAmount(), behavior: 'smooth' });
                });

                nextBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    grid.scrollBy({ left: getScrollAmount(), behavior: 'smooth' });
                });

                // Check and toggle arrow display depending on layout overflow
                const toggleArrowVisibility = () => {
                    const hasOverflow = grid.scrollWidth > grid.clientWidth;
                    prevBtn.style.display = hasOverflow ? 'flex' : 'none';
                    nextBtn.style.display = hasOverflow ? 'flex' : 'none';
                };

                toggleArrowVisibility();
                window.addEventListener('resize', toggleArrowVisibility);

                // Update button state (opacity) based on scroll boundaries
                const updateButtonStates = () => {
                    const scrollLeft = grid.scrollLeft;
                    const maxScroll = grid.scrollWidth - grid.clientWidth;

                    prevBtn.style.opacity = scrollLeft <= 2 ? '0.4' : '1';
                    prevBtn.style.pointerEvents = scrollLeft <= 2 ? 'none' : 'auto';

                    nextBtn.style.opacity = scrollLeft >= maxScroll - 2 ? '0.4' : '1';
                    nextBtn.style.pointerEvents = scrollLeft >= maxScroll - 2 ? 'none' : 'auto';
                };

                grid.addEventListener('scroll', updateButtonStates);
                updateButtonStates();

                // Trigger visibility check again after any image renders/font loads
                window.addEventListener('load', toggleArrowVisibility);
            }
        });
    };

    // Initialize all components
    const initAll = () => {
        attachExpandListeners();
        initSliders();
    };

    initAll();

    // Re-attach if blocks are loaded dynamically
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                initAll();
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
});
