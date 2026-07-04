/**
 * AEO Navigation Menu — Frontend View Script
 *
 * Handles:
 * 1. Scroll-based background opacity shift
 * 2. Mobile hamburger toggle → drawer open/close
 */
document.addEventListener('DOMContentLoaded', () => {
    const navBar = document.querySelector('.aeo-nav-bar');
    const burger = document.querySelector('.aeo-nav-burger');
    const drawer = document.querySelector('.aeo-nav-drawer');

    if (!navBar) return;

    // ── Scroll handler: darken nav bar on scroll ─────────────
    let ticking = false;
    const onScroll = () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                if (window.scrollY > 40) {
                    navBar.classList.add('aeo-nav-scrolled');
                } else {
                    navBar.classList.remove('aeo-nav-scrolled');
                }
                ticking = false;
            });
            ticking = true;
        }
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    // ── Mobile drawer toggle & close logic ────────────────────
    if (burger && drawer) {
        const closeBtn = drawer.querySelector('.aeo-nav-drawer-close');

        const openDrawer = () => {
            drawer.classList.add('open');
            drawer.setAttribute('aria-hidden', 'false');
            burger.classList.add('open');
            document.body.style.overflow = 'hidden';
            if (closeBtn) closeBtn.focus();
        };

        const closeDrawer = () => {
            drawer.classList.remove('open');
            drawer.setAttribute('aria-hidden', 'true');
            burger.classList.remove('open');
            document.body.style.overflow = '';
        };

        burger.addEventListener('click', () => {
            const isOpen = drawer.classList.contains('open');
            if (isOpen) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', closeDrawer);
        }

        // Close drawer when a link inside it is clicked
        drawer.querySelectorAll('a').forEach((link) => {
            link.addEventListener('click', () => {
                closeDrawer();
            });
        });

        // Close drawer when Escape key is pressed
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && drawer.classList.contains('open')) {
                closeDrawer();
            }
        });
    }
});
