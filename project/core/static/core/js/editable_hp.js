// HP field is only editable while its card is selected.
// Enter or blur commits; Escape cancels.

// Function that initializes all HP fields
function initHpFields(root) {
    // HP is initially readonly
    root.querySelectorAll(".hp-field").forEach(makeHpReadOnly);
}


export function setupEditableHp() {
    const board = document.getElementById("board");
    if (!board) return;

    initHpFields(board) // Initialize HP fields

    // Check for newly added characters and reinitialize HP
    new MutationObserver((mutations) => {
        for (const m of mutations) {
            for (const node of m.addedNodes) {
                if (node.nodeType !== Node.ELEMENT_NODE) continue;
                if (node.matches(".hp-field")) makeHpReadOnly(node);
                initHpFields(node);
            }
        }
    }).observe(board, { childList: true, subtree: true });

    board.addEventListener("combatant:selected", (e) => {
        const combatant = e.target.closest(".combatant");
        const hpField = combatant.querySelector(".hp-field");
        makeHpEditable(hpField, combatant.dataset.id);
    });

    board.addEventListener("combatant:deselected", (e) => {
        const combatant = e.target.closest(".combatant");
        const hpField = combatant.querySelector(".hp-field");
        const input = hpField.querySelector(".hp-input");

        //If HP is editable, commit the change and send the request
        if (input) commitHp(hpField, input.value, combatant.dataset.id)
    });

    board.addEventListener("keydown", (e) => {
        if (!e.target.matches(".hp-input")) return;

        if (e.key === "Enter") {
            e.target.blur();
        } 
    });
}

function makeHpReadOnly(el) {
    const { remaining, max } = el.dataset;
    el.innerHTML = `<strong>${remaining}</strong> / <span>${max}</span>`;
}

function makeHpEditable(el, combatant_id) {
    el.innerHTML = `
        <input type="number" class="form-control form-control-sm d-inline-block hp-input"
               style="width: 4rem" min="0" max="${el.dataset.max}" value="${el.dataset.remaining}">
        / <span>${el.dataset.max}</span>
    `;

    const input = el.querySelector(".hp-input");
    input.focus();
    input.select();

    input.addEventListener("blur", () => commitHp(el, input.value, combatant_id));
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") input.blur();
        else if (e.key === "Escape") makeHpReadOnly(el); // Revert
    });
}

// Updates HP value in the HTML
async function commitHp(el, val, combatant_id) {
    const newVal = parseInt(val, 10) // Parse value as int

    //If value isn't an int, just set HP field back to readonly and return
    if (Number.isNaN(newVal)) {
        makeHpReadOnly(el)
        return
    }

    //Otherwise, update it's values and send the request
    el.dataset.remaining = newVal
    await sendUpdateHpRequest(combatant_id, newVal, (actualVal) => {
        el.dataset.remaining = actualVal
    })
    makeHpReadOnly(el)
}

// Sends the PATCH request to the backend to update the HP
// Calls registered callback with the actual new HP if send HP and backend HP is mismatched
async function sendUpdateHpRequest(combatant_id, newHp, mismatched_value_cb) {
    const token = document.querySelector("[name=csrfmiddlewaretoken]").value;
    const combatant = document.querySelector(`[data-id="${combatant_id}"]`)
    const reqBody = {"remaining_hp": newHp}
    try {
        const res = await fetch(combatant.dataset.updateHpUrl, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": token,
            },
            body: JSON.stringify(reqBody),
        });
        if (!res.ok) {
            console.error("Failed to update HP", res.status);
        } else {
            const data = await res.json()
            const actualNewHp = data["remaining_hp"] 
            if (actualNewHp != newHp) {
                mismatched_value_cb(actualNewHp);
            }
        }
    } catch (err) {
        console.error("Network error updating character HP", err);
    }
}