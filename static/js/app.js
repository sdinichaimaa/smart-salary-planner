document.addEventListener("DOMContentLoaded", () => {
    const list = document.getElementById("responsibilities");
    const addButton = document.getElementById("add-responsibility");

    function bindRemoveButtons() {
        document.querySelectorAll(".remove-row").forEach(button => {
            button.onclick = () => {
                const rows = document.querySelectorAll(".responsibility-row");
                if (rows.length > 1) {
                    button.closest(".responsibility-row").remove();
                }
            };
        });
    }

    if (addButton && list) {
        addButton.addEventListener("click", () => {
            const row = document.createElement("div");
            row.className = "responsibility-row";
            row.innerHTML = `
                <input class="emoji-field" name="responsibility_icon[]" value="✨">
                <input name="responsibility_name[]" placeholder="Ex. Téléphone">
                <input name="responsibility_amount[]" type="number" min="0.01" step="0.01" placeholder="Montant">
                <button type="button" class="remove-row">×</button>
            `;
            list.appendChild(row);
            bindRemoveButtons();
        });
    }

    bindRemoveButtons();
});
