document.addEventListener('DOMContentLoaded', () => {
    const postTitle = document.querySelector('.wp-block-post-title');
    const heroHeader = document.querySelector('.wp-block-aeo-hero-gradient .aeo-hero-gradient-header, .wp-block-aeo-hero .aeo-hero-gradient-header');
    if (postTitle && heroHeader) {
        // If there's an existing h1 inside the hero, remove it to avoid duplicates
        const existingH1 = heroHeader.querySelector('h1');
        if (existingH1) {
            existingH1.remove();
        }

        // Move the post title element inside the hero header
        heroHeader.insertBefore(postTitle, heroHeader.firstChild);

        // Add styling class
        postTitle.classList.add('aeo-hero-gradient-dynamic-title');
    }
});
