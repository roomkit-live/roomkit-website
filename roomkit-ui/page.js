// Real screenshots from release v0.3.1. The controls change the gallery only.
(() => {
    const galleryTabs = [...document.querySelectorAll('.app-tabs [role="tab"]')];
    const galleryPanels = [...document.querySelectorAll('.app-panel')];
    function selectTab(tab) {
        galleryTabs.forEach((item, index) => {
            const selected = item === tab;
            item.setAttribute('aria-selected', String(selected));
            item.tabIndex = selected ? 0 : -1;
            galleryPanels[index].hidden = !selected;
        });
    }
    galleryTabs.forEach((tab, index) => {
        const panel = document.getElementById(tab.getAttribute('aria-controls'));
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('aria-labelledby', tab.id);
        panel.tabIndex = 0;
        tab.addEventListener('click', () => selectTab(tab));
        tab.addEventListener('keydown', (event) => {
            let next;
            if (event.key === 'ArrowRight') next = (index + 1) % galleryTabs.length;
            if (event.key === 'ArrowLeft') next = (index + galleryTabs.length - 1) % galleryTabs.length;
            if (event.key === 'Home') next = 0;
            if (event.key === 'End') next = galleryTabs.length - 1;
            if (next === undefined) return;
            event.preventDefault();
            selectTab(galleryTabs[next]);
            galleryTabs[next].focus();
        });
    });
    selectTab(galleryTabs[0]);
    document.querySelector('.app-tabs').hidden = false;

    const appearanceButtons = [...document.querySelectorAll('[data-theme]')];
    appearanceButtons.forEach((button) => {
        button.addEventListener('click', () => {
            appearanceButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
            document.querySelectorAll('[data-screenshot]').forEach((img) => {
                const path = `/roomkit-ui/screenshots/${img.dataset.screenshot}-${button.dataset.theme}.png`;
                img.src = path;
                img.closest('a').href = path;
            });
        });
    });
    document.querySelector('.app-appearance').hidden = false;
})();
