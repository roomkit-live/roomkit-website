// ========================================
// RoomKit Website JavaScript
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching for code examples
    initTabs();

    // Copy to clipboard functionality
    initCopyButtons();

    // Mobile navigation toggle
    initMobileNav();
});

// ========================================
// Tabs
// ========================================

function initTabs() {
    // Initialize each tab group independently
    const tabGroups = [
        { tabs: '.examples-tabs .tab', panels: '.examples-content .example-panel' },
        { tabs: '.orchestration-tabs .tab', panels: '.orchestration-panels .example-panel' },
    ];

    tabGroups.forEach(({ tabs: tabSelector, panels: panelSelector }) => {
        const tabs = document.querySelectorAll(tabSelector);
        const panels = document.querySelectorAll(panelSelector);

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetId = tab.dataset.tab;

                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                panels.forEach(panel => {
                    panel.classList.toggle('active', panel.id === targetId);
                });
            });
        });
    });
}

// ========================================
// Copy to Clipboard
// ========================================

function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');

    copyButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const text = btn.dataset.copy;

            try {
                await navigator.clipboard.writeText(text);

                // Visual feedback
                const originalHTML = btn.innerHTML;
                btn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M13 4L6 11L3 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                `;
                btn.style.color = '#22c55e';

                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });
}

// ========================================
// Mobile Navigation
// ========================================

function initMobileNav() {
    const toggle = document.querySelector('.nav-toggle');
    const nav = document.querySelector('.nav');

    if (toggle) {
        toggle.addEventListener('click', () => {
            nav.classList.toggle('nav-open');
        });
    }

    // Close mobile nav when a link is clicked
    document.querySelectorAll('.nav-links .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            nav.classList.remove('nav-open');
        });
    });
}

// ========================================
// Smooth scroll for anchor links
// ========================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Hero room demo: reveal events one by one, loop, respect reduced motion
(function () {
    const demo = document.querySelector('.room-demo-events');
    if (!demo) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const events = Array.from(demo.children);
    let timer = null;

    function stop() {
        if (timer) clearTimeout(timer);
        timer = null;
        demo.classList.remove('animated');
        events.forEach((e) => e.classList.remove('shown'));
    }

    function run() {
        demo.classList.add('animated');
        let i = 0;
        function next() {
            if (i < events.length) {
                events[i].classList.add('shown');
                i += 1;
                timer = setTimeout(next, 1100);
            } else {
                timer = setTimeout(() => {
                    events.forEach((e) => e.classList.remove('shown'));
                    i = 0;
                    timer = setTimeout(next, 700);
                }, 4200);
            }
        }
        timer = setTimeout(next, 400);
    }

    if (!reduced.matches) run();
    reduced.addEventListener('change', () => {
        stop();
        if (!reduced.matches) run();
    });
})();
