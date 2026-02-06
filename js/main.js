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
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.example-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetId = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update active panel
            panels.forEach(panel => {
                panel.classList.toggle('active', panel.id === targetId);
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
