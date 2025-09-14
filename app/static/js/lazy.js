document.addEventListener('DOMContentLoaded', function () {
    if ('loading' in HTMLImageElement.prototype) return;
    const imgs = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const img = entry.target;
            if (img.dataset.src) img.src = img.dataset.src;
            if (img.dataset.srcset) img.srcset = img.dataset.srcset;
            obs.unobserve(img);
        });
        }, { rootMargin: '200px' });
        imgs.forEach(img => io.observe(img));
    } else {
        setTimeout(()=> imgs.forEach(i => { if (i.dataset.src) i.src = i.dataset.src; }), 2000);
    }
});
  