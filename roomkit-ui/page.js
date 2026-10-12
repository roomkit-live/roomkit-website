// Progressive enhancement: screenshots and installation instructions work without JS.
(() => {
    const tabs = [...document.querySelectorAll('[role="tab"]')];
    function selectTab(tab) {
        tabs.forEach((item) => {
            const selected = item === tab;
            item.setAttribute("aria-selected", String(selected));
            item.tabIndex = selected ? 0 : -1;
            document.getElementById(item.getAttribute("aria-controls")).hidden = !selected;
        });
    }
    tabs.forEach((tab, index) => {
        tab.addEventListener("click", () => selectTab(tab));
        tab.addEventListener("keydown", (event) => {
            let next;
            if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
            if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
            if (event.key === "Home") next = 0;
            if (event.key === "End") next = tabs.length - 1;
            if (next === undefined) return;
            event.preventDefault();
            selectTab(tabs[next]);
            tabs[next].focus();
        });
    });
    selectTab(tabs[0]);
    document.querySelector(".preview-tabs").hidden = false;

    const themes = [...document.querySelectorAll("[data-theme]")];
    themes.forEach((button) =>
        button.addEventListener("click", () => {
            themes.forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
            document.querySelectorAll("[data-screenshot]").forEach((img) => {
                const path = `screenshots/${img.dataset.screenshot}-${button.dataset.theme}.png`;
                img.src = path;
                img.closest("a").href = path;
            });
        }),
    );
    document.querySelector(".theme-choice").hidden = false;

    const copy = document.getElementById("copy-install");
    if (navigator.clipboard) {
        copy.hidden = false;
        copy.addEventListener("click", async () => {
            const feedback = document.getElementById("copy-feedback");
            try {
                await navigator.clipboard.writeText(
                    document.getElementById("install-commands").textContent,
                );
                feedback.textContent = "Commands copied. Paste them into your terminal.";
            } catch {
                feedback.textContent = "Select the commands above and copy them manually.";
            }
        });
    }

    const nav = document.querySelector(".nav");
    const toggle = document.querySelector(".nav-toggle");
    function closeNavigation() {
        nav.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
    }
    toggle.addEventListener("click", () => {
        const open = nav.classList.toggle("nav-open");
        toggle.setAttribute("aria-expanded", String(open));
    });
    document
        .querySelectorAll(".nav a")
        .forEach((link) => link.addEventListener("click", closeNavigation));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && nav.classList.contains("nav-open")) {
            closeNavigation();
            toggle.focus();
        }
    });
})();
