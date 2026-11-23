import { rollDice } from "./dice.js";

const ATTACK_COUNT = /\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|\d+)(?=\s+attacks?\b)/gi;

export function splitAttackCount(description) {
    const parts = [];
    let cursor = 0;
    for (const match of description.matchAll(ATTACK_COUNT)) {
        if (match.index > cursor) {
            parts.push({ text: description.slice(cursor, match.index), bold: false });
        }
        parts.push({ text: match[0], bold: true });
        cursor = match.index + match[0].length;
    }
    if (cursor < description.length || parts.length === 0) {
        parts.push({ text: description.slice(cursor), bold: false });
    }
    return parts;
}

export function rollAttack(attack, mode = null) {
    let attackRoll = null;
    if (attack.attack_bonus !== null && attack.attack_bonus !== undefined) {
        const rolls = rollDice(20, mode ? 2 : 1).rolls;
        const selectedIndex = mode === "advantage"
            ? rolls.indexOf(Math.max(...rolls))
            : mode === "disadvantage"
                ? rolls.indexOf(Math.min(...rolls))
                : 0;
        const die = rolls[selectedIndex];
        attackRoll = {
            rolls,
            selectedIndex,
            die,
            bonus: attack.attack_bonus,
            total: die + attack.attack_bonus,
        };
    }

    const damageComponents = attack.damage_components.map((component) => {
        const match = /^(\d+)d(\d+)$/i.exec(component.damage_dice.trim());
        if (!match) {
            throw new Error(`Unsupported damage dice: ${component.damage_dice}`);
        }
        const roll = rollDice(Number(match[2]), Number(match[1]));
        const modifier = component.damage_modifier || 0;
        return {
            dice: component.damage_dice,
            rolls: roll.rolls,
            modifier,
            damage_type: component.damage_type,
            total: roll.total + modifier,
        };
    });

    return {
        attackRoll,
        dc: attack.dc,
        dcType: attack.dc_type,
        dcSuccess: attack.dc_success,
        damageComponents,
        damageTotal: damageComponents.reduce((sum, component) => sum + component.total, 0),
    };
}

export function setupAttacks() {
    const modal = document.getElementById("attackModal");
    const board = document.getElementById("board");
    if (!modal || !board) return;

    const content = modal.querySelector(".modal-content");
    const characterSelect = document.getElementById("attackCharacterSelect");
    const addCharacterButton = document.getElementById("addAttackCharacter");
    const characterList = document.getElementById("attackCharacterList");
    const emptyMessage = document.getElementById("attackNoCharacters");
    const status = document.getElementById("attackStatus");
    const rollButton = document.getElementById("rollAttacks");
    const characters = new Map();
    const selectedCharacters = new Set();
    const selectedAttacks = new Set();
    const attackModes = new Map();
    let fieldId = 0;

    function setStatus(message, isError = false) {
        status.textContent = message;
        status.classList.toggle("text-danger", isError);
    }

    function updateControls() {
        const hasSelection = characterList.querySelector(".attack-choice:checked") !== null;
        rollButton.disabled = !hasSelection;
        emptyMessage.hidden = selectedCharacters.size > 0;
    }

    function clearCharacterChoices(entryId) {
        const prefix = `${entryId}:`;
        for (const key of [...selectedAttacks]) {
            if (key.startsWith(prefix)) selectedAttacks.delete(key);
        }
        for (const key of [...attackModes.keys()]) {
            if (key.startsWith(prefix)) attackModes.delete(key);
        }
    }

    function makeField(labelText, name, type, options = {}) {
        const wrapper = document.createElement("div");
        wrapper.className = options.wrapperClass || "mb-2";
        const label = document.createElement("label");
        label.className = "form-label small mb-1";
        const input = document.createElement(type === "textarea" ? "textarea" : "input");
        input.className = "form-control form-control-sm";
        input.name = name;
        if (type !== "textarea") input.type = type;
        if (options.required) input.required = true;
        if (options.maxLength) input.maxLength = options.maxLength;
        if (options.placeholder) input.placeholder = options.placeholder;
        if (options.min !== undefined) input.min = options.min;
        if (options.step) input.step = options.step;
        input.id = `custom-attack-field-${fieldId++}`;
        label.htmlFor = input.id;
        label.textContent = labelText;
        wrapper.append(label, input);
        return { wrapper, input };
    }

    function makeSelect(labelText, name, choices) {
        const wrapper = document.createElement("div");
        wrapper.className = "mb-2";
        const label = document.createElement("label");
        label.className = "form-label small mb-1";
        const select = document.createElement("select");
        select.className = "form-select form-select-sm";
        select.name = name;
        select.id = `custom-attack-field-${fieldId++}`;
        label.htmlFor = select.id;
        label.textContent = labelText;
        for (const [value, text] of choices) {
            select.add(new Option(text, value));
        }
        wrapper.append(label, select);
        return { wrapper, select };
    }

    function createCustomAttackForm(character) {
        const form = document.createElement("form");
        form.className = "custom-attack-form border-top mt-3 pt-3";
        form.hidden = true;
        const title = document.createElement("h3");
        title.className = "h6";
        title.textContent = "Add a custom attack";
        const name = makeField("Attack name", "name", "text", { required: true, maxLength: 120 });
        const description = makeField("Description", "description", "textarea", { maxLength: 4000 });
        const bonus = makeField("Attack bonus (leave blank for a save DC)", "attack_bonus", "number", { step: "1" });
        const dc = makeField("Save DC (leave blank for an attack bonus)", "dc", "number", { min: "1", step: "1" });
        const ability = makeSelect("Saving throw ability", "dc_type", [
            ["DEX", "DEX"], ["STR", "STR"], ["CON", "CON"],
            ["INT", "INT"], ["WIS", "WIS"], ["CHA", "CHA"],
        ]);
        const success = makeSelect("On a successful save", "dc_success", [
            ["half", "Half damage"], ["none", "No damage"],
        ]);
        const damage = makeField("Damage formula (optional)", "damage_formula", "text", {
            maxLength: 50,
            placeholder: "e.g. 2d6 + 3",
        });
        const damageType = makeField("Damage type (optional)", "damage_type", "text", { maxLength: 50 });
        const fields = document.createElement("div");
        fields.className = "row row-cols-1 row-cols-sm-2 g-2";
        for (const field of [bonus.wrapper, dc.wrapper, ability.wrapper, success.wrapper, damage.wrapper, damageType.wrapper]) {
            field.classList.add("col");
            fields.append(field);
        }
        const error = document.createElement("p");
        error.className = "small text-danger mb-2";
        error.setAttribute("role", "alert");
        const save = document.createElement("button");
        save.className = "btn btn-sm btn-brass";
        save.type = "submit";
        save.textContent = "Save attack";
        form.append(title, name.wrapper, description.wrapper, fields, error, save);

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            error.textContent = "";
            if (!form.reportValidity()) return;

            const payload = {
                name: name.input.value.trim(),
                description: description.input.value,
                attack_bonus: bonus.input.value === "" ? null : Number(bonus.input.value),
                dc: dc.input.value === "" ? null : Number(dc.input.value),
                dc_type: ability.select.value,
                dc_success: success.select.value,
                damage_formula: damage.input.value.trim(),
                damage_type: damageType.input.value.trim(),
            };
            const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
            if (!token) {
                error.textContent = "Could not find the request security token.";
                return;
            }
            save.disabled = true;
            try {
                const response = await fetch(character.create_url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": token,
                    },
                    body: JSON.stringify(payload),
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
                form.reset();
                await loadCharacters();
                setStatus(`Saved ${result.name} for ${character.name}.`);
            } catch (requestError) {
                error.textContent = requestError.message || "Could not save this attack.";
            } finally {
                save.disabled = false;
            }
        });
        return form;
    }

    function makeCharacterSection(character) {
        const section = document.createElement("section");
        section.className = "border rounded p-3 mb-3";
        section.dataset.entryId = character.entry_id;
        const heading = document.createElement("div");
        heading.className = "d-flex align-items-center justify-content-between gap-2 mb-2";
        const name = document.createElement("h3");
        name.className = "h6 mb-0";
        name.textContent = character.name;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "btn btn-sm btn-outline-light";
        remove.textContent = "Remove";
        remove.setAttribute("aria-label", `Remove ${character.name} from attack selection`);
        remove.addEventListener("click", () => {
            selectedCharacters.delete(String(character.entry_id));
            clearCharacterChoices(character.entry_id);
            renderSelectedCharacters();
        });
        heading.append(name, remove);
        section.append(heading);

        if (character.attacks.length === 0) {
            const noAttacks = document.createElement("p");
            noAttacks.className = "small text-secondary mb-2";
            noAttacks.textContent = "No saved attacks yet.";
            section.append(noAttacks);
        } else {
            const list = document.createElement("div");
            list.className = "list-group";
            for (const attack of character.attacks) {
                if (attack.name.trim().toLowerCase() === "multiattack") {
                    const row = document.createElement("div");
                    row.className = "list-group-item";
                    const title = document.createElement("strong");
                    title.textContent = attack.name;
                    const description = document.createElement("p");
                    description.className = "small text-secondary mt-1 mb-0";
                    for (const part of splitAttackCount(attack.description)) {
                        if (part.bold) {
                            const count = document.createElement("strong");
                            count.textContent = part.text;
                            description.append(count);
                        } else {
                            description.append(document.createTextNode(part.text));
                        }
                    }
                    row.append(title, description);
                    list.append(row);
                    continue;
                }

                const key = `${character.entry_id}:${attack.id}`;
                const row = document.createElement("div");
                row.className = "list-group-item";
                const label = document.createElement("label");
                label.className = "form-check d-flex align-items-start gap-2 mb-0";
                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.className = "form-check-input mt-1 attack-choice";
                checkbox.checked = selectedAttacks.has(key);
                checkbox.attackData = attack;
                checkbox.dataset.key = key;
                const modeControls = document.createElement("fieldset");
                modeControls.className = "d-flex flex-wrap gap-3 border-0 p-0 mt-2 ms-4";
                const modeLegend = document.createElement("legend");
                modeLegend.className = "visually-hidden";
                modeLegend.textContent = `Roll modifier for ${attack.name}`;
                modeControls.append(modeLegend);
                const canModifyRoll = attack.attack_bonus !== null && attack.attack_bonus !== undefined;
                const modeInputs = new Map();
                for (const [mode, labelText] of [
                    ["advantage", "Advantage"],
                    ["disadvantage", "Disadvantage"],
                ]) {
                    const modeLabel = document.createElement("label");
                    modeLabel.className = "form-check d-inline-flex align-items-center gap-1 mb-0";
                    const modeInput = document.createElement("input");
                    modeInput.type = "checkbox";
                    modeInput.className = "form-check-input mt-0";
                    modeInput.id = `attack-${mode}-${character.entry_id}-${attack.id}`;
                    modeInput.checked = attackModes.get(key) === mode;
                    modeInput.disabled = !canModifyRoll;
                    const modeText = document.createElement("span");
                    modeText.className = "small";
                    modeText.textContent = labelText;
                    modeLabel.append(modeInput, modeText);
                    modeControls.append(modeLabel);
                    modeInputs.set(mode, modeInput);
                    modeInput.addEventListener("change", () => {
                        if (modeInput.checked) {
                            const otherMode = mode === "advantage" ? "disadvantage" : "advantage";
                            modeInputs.get(otherMode).checked = false;
                            attackModes.set(key, mode);
                        } else if (attackModes.get(key) === mode) {
                            attackModes.delete(key);
                        }
                        result.hidden = true;
                        result.replaceChildren();
                    });
                }
                const details = document.createElement("span");
                details.className = "flex-grow-1";
                const attackName = document.createElement("strong");
                attackName.textContent = attack.name;
                details.append(attackName);
                if (attack.description) {
                    const description = document.createElement("span");
                    description.className = "d-block small text-secondary";
                    description.textContent = attack.description;
                    details.append(description);
                }
                label.append(checkbox, details);
                const result = document.createElement("p");
                result.className = "small mt-2 mb-0 attack-result";
                result.hidden = true;
                result.setAttribute("aria-live", "polite");
                row.append(label, modeControls, result);
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) selectedAttacks.add(key);
                    else selectedAttacks.delete(key);
                    result.hidden = true;
                    result.textContent = "";
                    updateControls();
                });
                list.append(row);
            }
            section.append(list);
        }

        const customToggle = document.createElement("button");
        customToggle.type = "button";
        customToggle.className = "btn btn-sm btn-outline-light mt-3";
        customToggle.textContent = "Add custom attack";
        const customForm = createCustomAttackForm(character);
        customToggle.addEventListener("click", () => {
            customForm.hidden = !customForm.hidden;
            customToggle.textContent = customForm.hidden ? "Add custom attack" : "Cancel custom attack";
        });
        section.append(customToggle, customForm);
        return section;
    }

    function renderSelectedCharacters() {
        characterList.replaceChildren();
        for (const id of selectedCharacters) {
            const character = characters.get(id);
            if (character) characterList.append(makeCharacterSection(character));
        }
        updateControls();
    }

    function syncCharacterOptions() {
        const available = new Map(
            [...characters].map(([id, character]) => [id, character.name]),
        );
        for (const option of [...characterSelect.options].slice(1)) {
            if (!available.has(option.value)) option.remove();
        }
        for (const [id, name] of available) {
            const option = [...characterSelect.options].find((item) => item.value === id);
            if (option) option.textContent = name;
            else characterSelect.add(new Option(name, id));
        }
        for (const id of selectedCharacters) {
            if (!available.has(id)) {
                selectedCharacters.delete(id);
                clearCharacterChoices(id);
            }
        }
        renderSelectedCharacters();
    }

    async function loadCharacters() {
        const response = await fetch(content.dataset.loadUrl, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
        characters.clear();
        for (const character of result.characters) {
            characters.set(String(character.entry_id), character);
        }
        syncCharacterOptions();
    }

    addCharacterButton.addEventListener("click", () => {
        const id = characterSelect.value;
        if (!id || !characters.has(id)) {
            setStatus("Choose a character from this encounter first.", true);
            return;
        }
        selectedCharacters.add(id);
        setStatus("");
        renderSelectedCharacters();
        characterSelect.value = "";
    });

    rollButton.addEventListener("click", () => {
        const choices = [...characterList.querySelectorAll(".attack-choice:checked")];
        if (choices.length === 0) {
            setStatus("Select at least one attack to roll.", true);
            return;
        }
        setStatus("");
        for (const choice of choices) {
            const output = choice.closest(".list-group-item").querySelector(".attack-result");
            try {
                const result = rollAttack(choice.attackData, attackModes.get(choice.dataset.key));
                renderAttackResult(output, result);
                const sendButton = document.createElement("button");
                sendButton.type = "button";
                sendButton.className = "btn btn-sm btn-outline-light mt-2";
                sendButton.textContent = "Send to Defend";
                sendButton.addEventListener("click", () => {
                    const transfer = buildDefendTransfer(result);
                    document.dispatchEvent(new CustomEvent("attack:send-to-defend", {
                        detail: transfer,
                    }));
                    bootstrap.Modal.getOrCreateInstance(modal).hide();
                    bootstrap.Modal.getOrCreateInstance(
                        document.getElementById("defendModal"),
                    ).show();
                });
                output.append(sendButton);
                output.classList.remove("text-danger");
            } catch (error) {
                output.textContent = `Could not roll this attack: ${error.message || "invalid attack data"}`;
                output.classList.add("text-danger");
            }
            output.hidden = false;
        }
    });

    modal.addEventListener("show.bs.modal", () => {
        setStatus("");
        loadCharacters().catch((error) => {
            setStatus(error.message || "Could not load encounter attacks.", true);
        });
    });
    new MutationObserver(() => {
        loadCharacters().catch((error) => {
            setStatus(error.message || "Could not refresh encounter characters.", true);
        });
    }).observe(board, { childList: true });
    board.addEventListener("combatants:cleared", () => {
        selectedCharacters.clear();
        selectedAttacks.clear();
        attackModes.clear();
        renderSelectedCharacters();
    });
    board.addEventListener("combatant:removed", () => {
        loadCharacters().catch((error) => {
            setStatus(error.message || "Could not refresh encounter characters.", true);
        });
    });
    updateControls();
}

export function buildDefendTransfer(result) {
    return {
        damage: result.damageTotal,
        mode: result.dc !== null && result.dc !== undefined ? "save" : "attack",
        attackRoll: result.attackRoll?.total ?? null,
        dc: result.dc ?? null,
        dcType: result.dcType || "",
        dcSuccess: result.dcSuccess || "",
        halfOnSave: result.dcSuccess === "half",
    };
}

export function formatAttackResult(result) {
    const lines = [];
    if (result.attackRoll) {
        lines.push(
            {
                prefix: "Attack Roll: (",
                rolls: result.attackRoll.rolls,
                selectedIndex: result.attackRoll.selectedIndex,
                middle: `) ${formatModifier(result.attackRoll.bonus)} = `,
                value: result.attackRoll.total,
                className: "attack-roll-total",
            },
        );
    } else if (result.dc !== null && result.dc !== undefined) {
        const effect = result.dcSuccess === "half"
            ? "; half damage on save"
            : result.dcSuccess === "none"
                ? "; no damage on save"
                : "";
        lines.push({ text: `Save DC ${result.dc} ${result.dcType}${effect}` });
    } else {
        lines.push({ text: "No attack bonus or save DC recorded." });
    }

    if (result.damageComponents.length === 0) {
        lines.push({ text: "No damage dice recorded." });
    } else {
        for (const component of result.damageComponents) {
            lines.push(
                {
                    prefix: `Damage: ${component.dice} (${component.rolls.join(" + ")}) ${formatModifier(component.modifier)} = `,
                    value: component.total,
                    suffix: component.damage_type ? ` ${component.damage_type}` : "",
                    className: "attack-damage-total",
                },
            );
        }
    }
    return lines;
}

function renderAttackResult(output, result) {
    output.replaceChildren();
    for (const line of formatAttackResult(result)) {
        const element = document.createElement("span");
        element.className = "d-block";
        if (line.className) {
            if (line.rolls) {
                element.append(document.createTextNode(line.prefix));
                line.rolls.forEach((roll, index) => {
                    if (index > 0) element.append(document.createTextNode(", "));
                    if (line.rolls.length > 1 && index === line.selectedIndex) {
                        const selected = document.createElement("strong");
                        selected.className = "attack-die-used";
                        selected.textContent = String(roll);
                        element.append(selected);
                    } else {
                        element.append(document.createTextNode(String(roll)));
                    }
                });
                element.append(document.createTextNode(line.middle));
            } else {
                element.append(document.createTextNode(line.prefix));
            }
            const total = document.createElement("strong");
            total.className = line.className;
            total.textContent = String(line.value);
            element.append(
                total,
                document.createTextNode(line.suffix || ""),
            );
        } else {
            element.textContent = line.text;
        }
        output.append(element);
    }
}

function formatModifier(modifier) {
    return `${modifier >= 0 ? "+" : "-"} ${Math.abs(modifier)}`;
}
