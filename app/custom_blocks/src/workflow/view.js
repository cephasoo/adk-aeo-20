/**
 * AEO Agentic Workflow — Frontend Stepper Interactivity
 *
 * Implements hover/click triggers on timeline step nodes to dynamically shift
 * glowing active states and highlight path progress.
 */
document.addEventListener('DOMContentLoaded', () => {
    const timelines = document.querySelectorAll('.wp-block-aeo-workflow');

    timelines.forEach((timeline) => {
        const steps = timeline.querySelectorAll('.aeo-workflow-step');

        steps.forEach((step, index) => {
            const node = step.querySelector('.aeo-step-node');
            const card = step.querySelector('.aeo-step-card');

            function activateStep() {
                // Clear active states on all steps
                steps.forEach((s) => {
                    const n = s.querySelector('.aeo-step-node');
                    const c = s.querySelector('.aeo-step-card');
                    if (n) n.classList.remove('active');
                    if (c) c.classList.remove('active');
                });

                // Activate selected step
                if (node) node.classList.add('active');
                if (card) card.classList.add('active');
            }

            if (node) {
                // Trigger on hover and click
                node.addEventListener('mouseenter', activateStep);
                node.addEventListener('click', activateStep);
            }
        });
    });
});
