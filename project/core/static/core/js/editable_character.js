const SAVE_FIELDS = new Set([
    "strength_save_bonus",
    "dexterity_save_bonus",
    "constitution_save_bonus",
    "intelligence_save_bonus",
    "wisdom_save_bonus",
    "charisma_save_bonus",
]);
const INTEGER_FIELDS = new Set([...SAVE_FIELDS, "armor_class"]);

export function setupEditableCharacterFields() {
    const board = document.getElementById("board");
    if (!board) return;

    board.addEventListener("click", (event) => {
        const button = event.target.closest(".editable-character-field");
        if (!button || !board.contains(button)) return;
        beginEdit(button);
    });
}

function beginEdit(button) {
    const field = button.dataset.characterField;
    if (field !== "name" && !INTEGER_FIELDS.has(field)) return;

    const card = button.closest(".combatant");
    const status = card.querySelector(".character-edit-status");
    status.hidden = true;
    status.textContent = "";

    const input = document.createElement("input");
    input.type = field === "name" ? "text" : "number";
    input.className = `character-field-input${field === "name" ? " name" : ""}`;
    input.value = button.textContent.trim();
    input.setAttribute("aria-label", button.getAttribute("aria-label"));
    if (field === "name") {
        input.maxLength = 120;
    } else {
        input.step = "1";
        if (field === "armor_class") input.min = "1";
    }

    button.replaceWith(input);
    input.focus();
    input.select();

    let requestPending = false;
    let canceled = false;

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            input.blur();
        } else if (event.key === "Escape") {
            canceled = true;
            status.hidden = true;
            status.textContent = "";
            input.replaceWith(button);
        }
    });

    input.addEventListener("blur", () => {
        if (canceled || requestPending) return;
        void saveCharacterField(input, button, card, status, field, () => {
            requestPending = false;
        }, () => {
            requestPending = true;
        });
    });
}

async function saveCharacterField(input, button, card, status, field, onFailure, onPending) {
    const value = field === "name" ? input.value.trim() : Number(input.value);
    if (field === "name" && (!value || value.length > 120)) {
        showEditError(status, "Name must contain 1 to 120 characters.");
        input.focus();
        return;
    }
    if (field !== "name" && (!Number.isSafeInteger(value) || input.value.trim() === "")) {
        showEditError(
            status,
            field === "armor_class"
                ? "Armor class must be a positive whole number."
                : "Saving throw bonus must be a whole number.",
        );
        input.focus();
        return;
    }
    if (field === "armor_class" && value < 1) {
        showEditError(status, "Armor class must be a positive whole number.");
        input.focus();
        return;
    }

    const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
    if (!token) {
        showEditError(status, "Could not find the request security token.");
        onFailure();
        return;
    }

    input.disabled = true;
    onPending();
    try {
        const response = await fetch(card.dataset.updateCharacterUrl, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": token,
            },
            body: JSON.stringify({ [field]: value }),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || `Could not save changes (HTTP ${response.status}).`);
        }

        const savedValue = result[field];
        if (typeof savedValue !== (field === "name" ? "string" : "number")) {
            throw new Error("The server returned an invalid character update.");
        }
        const display = button.querySelector(".editable-character-value") || button;
        display.textContent = savedValue;
        if (field === "name") {
            button.setAttribute("aria-label", `Edit combatant name: ${savedValue}`);
        } else if (field === "armor_class") {
            card.dataset.armorClass = savedValue;
        } else {
            const ability = field.replace("_save_bonus", "");
            card.dataset[`${ability}SaveBonus`] = savedValue;
            card.dataset[`save${ability[0].toUpperCase()}${ability.slice(1)}Bonus`] = savedValue;
        }
        input.replaceWith(button);
        status.hidden = true;
    } catch (error) {
        input.disabled = false;
        showEditError(status, error.message || "Could not save changes. Try again.");
        onFailure();
        input.focus();
        input.select();
    }
}

function showEditError(status, message) {
    status.textContent = message;
    status.hidden = false;
}
