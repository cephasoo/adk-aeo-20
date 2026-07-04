/**
 * AEO ROI Calculator — Frontend Interactivity Script
 *
 * Captures slider input changes and dynamically updates Net Annual Savings,
 * Weekly Savings, and Hours Reclaimed metrics with standard formatting.
 */
document.addEventListener('DOMContentLoaded', () => {
    const calcs = document.querySelectorAll('.wp-block-aeo-calculator');

    calcs.forEach((calc) => {
        const hoursSlider = calc.querySelector('.slider-hours');
        const rateSlider = calc.querySelector('.slider-rate');
        const efficiencySlider = calc.querySelector('.slider-efficiency');

        const hoursVal = calc.querySelector('.val-hours');
        const rateVal = calc.querySelector('.val-rate');
        const efficiencyVal = calc.querySelector('.val-efficiency');

        const annualSavingsMetric = calc.querySelector('.metric-annual-savings');
        const weeklySavingsMetric = calc.querySelector('.metric-weekly-savings');
        const hoursReclaimedMetric = calc.querySelector('.metric-hours-reclaimed');

        // Extract maintenance cost constant from dataset
        const maintenanceCost = parseFloat(calc.dataset.maintenance || 2500);

        function updateROI() {
            if (!hoursSlider || !rateSlider || !efficiencySlider) return;

            const hours = parseFloat(hoursSlider.value);
            const rate = parseFloat(rateSlider.value);
            const efficiency = parseFloat(efficiencySlider.value) / 100;

            // Update range indicators
            if (hoursVal) hoursVal.textContent = `${hours} hrs`;
            if (rateVal) rateVal.textContent = `$${rate}/hr`;
            if (efficiencyVal) efficiencyVal.textContent = `${Math.round(efficiency * 100)}%`;

            // Calculate Metrics
            const weeklySavings = Math.round(hours * rate * efficiency);
            const annualSavings = Math.round((weeklySavings * 52) - maintenanceCost);
            const hoursReclaimed = Math.round(hours * 52 * efficiency);

            // Display formatted outputs
            if (annualSavingsMetric) {
                annualSavingsMetric.textContent = `$${annualSavings.toLocaleString()}`;
            }
            if (weeklySavingsMetric) {
                weeklySavingsMetric.textContent = `$${weeklySavings.toLocaleString()}`;
            }
            if (hoursReclaimedMetric) {
                hoursReclaimedMetric.textContent = `${hoursReclaimed.toLocaleString()} hrs`;
            }
        }

        // Bind input and change listeners for continuous update
        if (hoursSlider) {
            hoursSlider.addEventListener('input', updateROI);
            hoursSlider.addEventListener('change', updateROI);
        }
        if (rateSlider) {
            rateSlider.addEventListener('input', updateROI);
            rateSlider.addEventListener('change', updateROI);
        }
        if (efficiencySlider) {
            efficiencySlider.addEventListener('input', updateROI);
            efficiencySlider.addEventListener('change', updateROI);
        }

        // Run initial configuration
        updateROI();
    });
});
