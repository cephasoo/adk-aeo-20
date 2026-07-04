/**
 * AEO Metrics Grid — Interactive Count-Up Animation
 *
 * Runs a smooth requestAnimationFrame count-up animation on numeric stat values
 * when the metrics block scrolls into the browser viewport.
 */
document.addEventListener('DOMContentLoaded', () => {
    const statElements = document.querySelectorAll('.aeo-metric-value-text');

    if (!('IntersectionObserver' in window)) {
        // Fallback for older browsers
        return;
    }

    const observer = new IntersectionObserver((entries, self) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                animateCount(entry.target);
                self.unobserve(entry.target); // Animate only once
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });

    statElements.forEach((el) => {
        // Store original text value
        el.dataset.targetVal = el.textContent.trim();
        // Parse numbers vs text
        const matches = el.dataset.targetVal.match(/^([^0-9.-]*)([0-9.-]+)([^0-9]*)$/);

        if (matches) {
            el.dataset.prefix = matches[1] || '';
            el.dataset.number = parseFloat(matches[2]);
            el.dataset.suffix = matches[3] || '';

            // Set initial state to 0 formatted
            el.textContent = el.dataset.prefix + '0' + el.dataset.suffix;
            observer.observe(el);
        }
    });

    function animateCount(el) {
        const targetNum = parseFloat(el.dataset.number);
        const prefix = el.dataset.prefix;
        const suffix = el.dataset.suffix;
        const duration = 1500; // 1.5 seconds
        const startTime = performance.now();
        const isDecimal = el.dataset.targetVal.includes('.');

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // EaseOutQuad formula
            const easeProgress = progress * (2 - progress);

            const currentNum = easeProgress * targetNum;

            // Format number decimal precision
            let displayNum = '';
            if (isDecimal) {
                // Match decimal places count of original value
                const decimals = el.dataset.targetVal.split('.')[1].replace(/[^0-9]/g, '').length;
                displayNum = currentNum.toFixed(decimals);
            } else {
                displayNum = Math.floor(currentNum).toLocaleString();
            }

            el.textContent = prefix + displayNum + suffix;

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                // Guarantee exact end value
                el.textContent = el.dataset.targetVal;
            }
        }

        requestAnimationFrame(update);
    }
});
