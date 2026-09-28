document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".primary-btn, .secondary-btn, .ghost-btn").forEach(el => {
        el.addEventListener("mousedown", () => el.style.transform = "scale(.98)");
        el.addEventListener("mouseup", () => el.style.transform = "");
        el.addEventListener("mouseleave", () => el.style.transform = "");
    });
});
