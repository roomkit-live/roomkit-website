// Shared navigation and copy controls for both preview pages.
document.documentElement.classList.add('js-enabled');

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#main-nav');
menuButton.hidden = false;

function closeMenu({ restoreFocus = false } = {}) {
    navigation.classList.remove('is-open');
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.querySelector('span').textContent = '+';
    if (restoreFocus) menuButton.focus();
}

menuButton.addEventListener('click', () => {
    const expanded = menuButton.getAttribute('aria-expanded') !== 'true';
    navigation.classList.toggle('is-open', expanded);
    menuButton.setAttribute('aria-expanded', String(expanded));
    menuButton.querySelector('span').textContent = expanded ? '−' : '+';
});
navigation.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
});
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        closeMenu({ restoreFocus: true });
    }
});

const copyStatus = document.querySelector('#copy-status');
document.querySelectorAll('[data-copy], [data-copy-target]').forEach((button) => {
    button.hidden = false;
    const originalContent = button.innerHTML;
    const originalLabel = button.getAttribute('aria-label');
    button.addEventListener('click', async () => {
        button.disabled = true;
        copyStatus.textContent = '';
        const target = button.dataset.copyTarget
            ? document.querySelector(button.dataset.copyTarget)
            : button.parentElement.querySelector('code');
        const text = button.dataset.copy ?? target.textContent;
        try {
            await navigator.clipboard.writeText(text);
            button.classList.add('is-copied');
            button.setAttribute('aria-label', 'Copied to clipboard');
            button.innerHTML = '<span aria-hidden="true">✓</span>';
            copyStatus.textContent = 'Copied to clipboard.';
        } catch {
            if (target) {
                const range = document.createRange();
                range.selectNodeContents(target);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
            }
            copyStatus.textContent = 'Copy is unavailable. Select the command and press Control+C or Command+C.';
        }
        window.setTimeout(() => {
            button.classList.remove('is-copied');
            button.innerHTML = originalContent;
            if (originalLabel) button.setAttribute('aria-label', originalLabel);
            else button.removeAttribute('aria-label');
            button.disabled = false;
        }, 2000);
    });
});
