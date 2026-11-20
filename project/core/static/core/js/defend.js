const ABILITIES = {
    strength: "STR",
    dexterity: "DEX",
    constitution: "CON",
    intelligence: "INT",
    wisdom: "WIS",
    charisma: "CHA",
};

export function setupDefend() {
    const form = document.getElementById("defendForm");
    const board = document.getElementById("board");
    if (!form || !board) return;

    const targetSelect = document.getElementById("defendTargetSelect");
    const targetList = document.getElementById("defendTargetList");
    const emptyMessage = document.getElementById("defendNoTargets");
    const applyButton = document.getElementById("applyDefend");
    const status = document.getElementById("defendStatus");
    const attackFields = document.getElementById("defendAttackFields");
    const saveFields = document.getElementById("defendSaveFields");
    const attackRollInput = document.getElementById("defendAttackRoll");
    const dcInput = document.getElementById("defendDc");
    const damageInput = document.getElementById("defendDamage");
    const selectedTargets = new Map();

    function syncTargetOptions() {
        const cards = [...board.querySelectorAll(".combatant")];
        const available = new Set(cards.map((card) => card.dataset.id));
        for (const option of [...targetSelect.options].slice(1)) {
            if (!available.has(option.value)) option.remove();
        }
        for (const card of cards) {
            const existingOption = [...targetSelect.options].find((item) => item.value === card.dataset.id);
            if (existingOption) {
                existingOption.textContent = card.querySelector(".name")?.textContent.trim() || "Unnamed combatant";
                continue;
            }
            const option = document.createElement("option");
            option.value = card.dataset.id;
            option.textContent = card.querySelector(".name")?.textContent.trim() || "Unnamed combatant";
            targetSelect.append(option);
        }
    }

    function updateControls() {
        const mode = form.elements.defendMode.value;
        attackFields.hidden = mode !== "attack";
        saveFields.hidden = mode !== "save";
        attackRollInput.required = mode === "attack" && Number(damageInput.value) > 0;
        dcInput.required = mode === "save" && Number(damageInput.value) >= 0;
        applyButton.disabled = selectedTargets.size === 0;
        emptyMessage.hidden = selectedTargets.size > 0;
    }

    function addTargetRow(card) {
        const id = card.dataset.id;
        if (selectedTargets.has(id)) return false;

        const item = document.createElement("li");
        item.className = "list-group-item d-flex flex-wrap align-items-center gap-2";
        item.dataset.targetId = id;

        const name = document.createElement("strong");
        name.className = "defend-target-name me-auto";
        name.textContent = card.querySelector(".name")?.textContent.trim() || "Unnamed combatant";
        const ac = document.createElement("span");
        ac.className = "small text-secondary";
        ac.textContent = `AC ${card.dataset.armorClass}`;
        const traits = document.createElement("div");
        traits.className = "defend-target-traits";

        for (const [key, label] of [
            ["resistant", "Is Resistant"],
            ["immune", "Is Immune"],
            ["vulnerable", "Is Vulnerable"],
            ["advantage", "Has Advantage"],
        ]) {
            const wrapper = document.createElement("div");
            wrapper.className = "form-check form-check-inline";
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.className = "form-check-input";
            checkbox.id = `defend-${id}-${key}`;
            checkbox.dataset.trait = key;
            const labelElement = document.createElement("label");
            labelElement.className = "form-check-label small";
            labelElement.htmlFor = checkbox.id;
            labelElement.textContent = label;
            wrapper.append(checkbox, labelElement);
            traits.append(wrapper);
        }

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn-sm btn-outline-secondary";
        remove.textContent = "Remove";
        remove.setAttribute("aria-label", `Remove ${name.textContent}`);
        remove.addEventListener("click", () => {
            selectedTargets.delete(id);
            item.remove();
            updateControls();
        });

        item.append(name, ac, traits, remove);
        targetList.append(item);
        selectedTargets.set(id, card);
        updateControls();
        return true;
    }

    const addTargetButton = document.getElementById("addDefendTarget");
    addTargetButton.addEventListener("click", (event) => {
        event.preventDefault();
        syncTargetOptions();
        const id = targetSelect.value;
        const card = [...board.querySelectorAll(".combatant")].find(
            (combatant) => combatant.dataset.id === id,
        );
        if (!id || !card) {
            status.textContent = "Choose a creature from the encounter first.";
            status.classList.add("text-danger");
            return;
        }

        status.classList.remove("text-danger");
        status.textContent = addTargetRow(card)
            ? ""
            : `${card.querySelector(".name")?.textContent.trim() || "This creature"} is already in the target list.`;
        targetSelect.value = "";
        updateControls();
    });

    targetSelect.addEventListener("change", () => {
        status.classList.remove("text-danger");
        status.textContent = "";
        updateControls();
    });

    form.querySelectorAll('input[name="defendMode"]').forEach((input) => {
        input.addEventListener("change", updateControls);
    });
    damageInput.addEventListener("input", updateControls);
    new MutationObserver(syncTargetOptions).observe(board, { childList: true, subtree: true });
    syncTargetOptions();
    updateControls();

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        status.classList.remove("text-danger");
        status.textContent = "";
        if (selectedTargets.size === 0) {
            status.textContent = "Add at least one target.";
            return;
        }
        if (!form.reportValidity()) return;

        const damage = Number(damageInput.value);
        if (!Number.isSafeInteger(damage)) {
            status.textContent = "Damage or healing must be a whole number.";
            status.classList.add("text-danger");
            return;
        }

        const mode = form.elements.defendMode.value;
        const attackRoll = Number(attackRollInput.value);
        const dc = Number(dcInput.value);
        const ability = form.elements.saveAbility.value;
        const halfOnSave = document.getElementById("halfDamageOnSave").checked;
        const outcomes = [];
        let hadError = false;
        applyButton.disabled = true;
        form.querySelectorAll("input, button, select").forEach((control) => {
            if (control !== applyButton) control.disabled = true;
        });

        try {
            for (const [id, card] of selectedTargets) {
                const item = targetList.querySelector(`[data-target-id="${CSS.escape(id)}"]`);
                const traits = new Set(
                    [...item.querySelectorAll("[data-trait]:checked")].map((checkbox) => checkbox.dataset.trait),
                );
                let amount = damage;
                let detail = "Applied";

                if (damage > 0 && mode === "attack" && attackRoll <= Number(card.dataset.armorClass)) {
                    outcomes.push(`${card.querySelector(".name").textContent.trim()}: Miss (AC ${card.dataset.armorClass}).`);
                    continue;
                }

                if (damage >= 0 && mode === "save") {
                    const saveRolls = [rollD20()];
                    if (traits.has("advantage")) saveRolls.push(rollD20());
                    const saveRoll = Math.max(...saveRolls);
                    const bonus = Number(card.dataset[`${ability}SaveBonus`]);
                    const saved = saveRoll + bonus >= dc;
                    const rollSummary = saveRolls.length > 1
                        ? `${saveRolls.join(" / ")}; used ${saveRoll}`
                        : String(saveRoll);
                    detail = `${saved ? "Saved" : "Failed save"} (${ABILITIES[ability]} ${rollSummary} ${bonus >= 0 ? "+" : ""}${bonus} vs DC ${dc})`;
                    if (saved) amount = halfOnSave ? Math.floor(amount / 2) : 0;
                }

                if (amount > 0) {
                    if (traits.has("immune")) amount = 0;
                    else if (traits.has("resistant") !== traits.has("vulnerable")) {
                        amount = traits.has("resistant") ? Math.max(1, Math.floor(amount / 2)) : amount * 2;
                    }
                }

                const hpField = card.querySelector(".hp-field");
                const currentHp = Number(hpField.dataset.remaining);
                const maxHp = Number(hpField.dataset.max);
                const newHp = Math.min(maxHp, Math.max(0, currentHp - amount));
                if (newHp !== currentHp) {
                    const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
                    if (!token) throw new Error("Could not find the request security token.");
                    try {
                        const response = await fetch(card.dataset.updateHpUrl, {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json", "X-CSRFToken": token },
                            body: JSON.stringify({ remaining_hp: newHp }),
                        });
                        const result = await response.json();
                        if (!response.ok) {
                            throw new Error(result.error || `HTTP ${response.status}`);
                        }
                        updateHpDisplay(card, result.remaining_hp);
                    } catch (error) {
                        hadError = true;
                        outcomes.push(`${card.querySelector(".name").textContent.trim()}: Could not update HP (${error.message || "request failed"}).`);
                        continue;
                    }
                }

                const effect = amount < 0 ? `Healed ${Math.abs(amount)}` : `Took ${amount} damage`;
                outcomes.push(`${card.querySelector(".name").textContent.trim()}: ${detail}; ${effect}.`);
            }
            status.textContent = outcomes.join(" ");
            if (hadError) status.classList.add("text-danger");
        } catch (error) {
            status.textContent = error.message || "Could not apply the effect to all targets.";
            status.classList.add("text-danger");
        } finally {
            form.querySelectorAll("input, button, select").forEach((control) => {
                control.disabled = false;
            });
            applyButton.disabled = selectedTargets.size === 0;
        }
    });
}

function rollD20() {
    return Math.floor(Math.random() * 20) + 1;
}

function updateHpDisplay(card, remainingHp) {
    const hpField = card.querySelector(".hp-field");
    const maxHp = Number(hpField.dataset.max);
    hpField.dataset.remaining = remainingHp;
    const input = hpField.querySelector(".hp-input");
    if (input) input.value = remainingHp;
    else hpField.innerHTML = `<strong>${remainingHp}</strong> / <span>${maxHp}</span>`;

    const fill = card.querySelector(".hp-fill");
    const ratio = maxHp > 0 ? Math.max(0, Math.min(remainingHp / maxHp, 1)) : 0;
    fill.style.width = `${ratio * 100}%`;
    fill.style.backgroundColor = `hsl(${120 * ratio} 70% 45%)`;
}
