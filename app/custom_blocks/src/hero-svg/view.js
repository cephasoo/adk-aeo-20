document.addEventListener('DOMContentLoaded', () => {
    const postTitle = document.querySelector('.wp-block-post-title');
    const heroHeader = document.querySelector('.wp-block-aeo-hero-svg .aeo-hero-gradient-header');
    if (postTitle && heroHeader) {
        const existingH1 = heroHeader.querySelector('h1');
        if (existingH1) {
            existingH1.remove();
        }
        heroHeader.insertBefore(postTitle, heroHeader.firstChild);
        postTitle.classList.add('aeo-hero-gradient-dynamic-title');
    }
});
