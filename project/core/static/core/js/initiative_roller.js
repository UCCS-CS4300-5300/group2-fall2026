import { rollDice } from "./dice.js";

export function orderCombatants(cards) {
    return [...cards].sort((a, b) => {
        const first = Number(a.dataset.initValue);
        const second = Number(b.dataset.initValue);
        if (first === 0 && second !== 0) return 1;
        if (second === 0 && first !== 0) return -1;
        return second - first || Number(a.dataset.id) - Number(b.dataset.id);
    });
}

export function setupInitiativeRoller() {
    const board = document.getElementById("board");
    const rollButton = document.getElementById("initBtn");
    const nextButton = document.getElementById("nextBtn");
    const status = document.getElementById("turnInfo");
    const hint = document.getElementById("hint");
    const list = document.getElementById("initiativeOrder");
    const empty = document.getElementById("initiativeEmpty");
    let turn = JSON.parse(document.getElementById("initialTurn").textContent);
    let saving = false;

    function showOrder() {
        const focusedId = list.contains(document.activeElement) ? document.activeElement.id : null;
        list.replaceChildren();
        const cards = orderCombatants(board.querySelectorAll(".combatant"));
        empty.hidden = cards.length > 0;
        for (const card of cards) {
            const name = card.querySelector(".name").textContent;
            const score = Number(card.dataset.initValue);
            const row = document.createElement("li");
            row.className = "initiative-entry";
            const label = document.createElement("label");
            const input = document.createElement("input");
            input.id = `initiative-${card.dataset.id}`;
            input.type = "number";
            input.className = "form-control form-control-sm initiative-score";
            input.min = "0";
            input.max = "20";
            input.step = "1";
            input.value = score === 0 ? "" : score;
            input.placeholder = "—";
            input.setAttribute("aria-label", `Initiative for ${name}`);
            input.readOnly = saving;
            label.htmlFor = input.id;
            label.textContent = name;
            row.append(label, input);

            if (Number(card.dataset.id) === turn.active_id) {
                row.setAttribute("aria-current", "true");
                const current = document.createElement("span");
                current.className = "initiative-note";
                current.textContent = "Current turn";
                label.append(current);
            } else if (score === 0) {
                const waiting = document.createElement("span");
                waiting.className = "initiative-note";
                waiting.textContent = "Waiting for initiative";
                label.append(waiting);
            }

            input.addEventListener("blur", () => {
                if (saving) return;
                const value = input.value === "" ? 0 : Number(input.value);
                if (input.validity.badInput || !Number.isInteger(value) || value < 0 || value > 20) {
                    hint.textContent = "Initiative must be a whole number from 0 to 20.";
                    input.value = score === 0 ? "" : score;
                    return;
                }
                if (value === score) return;
                saveTurn(card.dataset.updateInitiativeUrl, {
                    initiative: value,
                    turn_version: turn.turn_version,
                }, "PATCH");
            });
            input.addEventListener("keydown", (event) => {
                if (event.key === "Escape") input.value = score === 0 ? "" : score;
                if (event.key === "Enter" || event.key === "Escape") {
                    event.preventDefault();
                    input.blur();
                }
            });
            list.append(row);
        }
        if (focusedId) document.getElementById(focusedId)?.focus();
    }

    function showTurn() {
        let activeCard;
        for (const card of board.querySelectorAll(".combatant")) {
            const id = card.dataset.id;
            const score = turn.rolls[id];
            if (score !== undefined) {
                const badge = card.querySelector(".init-badge");
                card.dataset.initValue = score;
                badge.textContent = score;
                badge.style.visibility = score === 0 ? "hidden" : "visible";
            }

            if (Number(id) === turn.active_id) {
                activeCard = card;
                card.setAttribute("aria-current", "true");
            } else {
                card.removeAttribute("aria-current");
            }
        }

        rollButton.disabled = saving;
        nextButton.disabled = saving || !activeCard;
        if (activeCard) {
            const name = activeCard.querySelector(".name").textContent;
            status.textContent = `Round ${turn.round} · ${name}’s turn`;
        } else if (turn.active_id !== null) {
            status.textContent = "Reload to see the current combatant.";
        } else {
            status.textContent = "Roll initiative to begin";
        }
        showOrder();
    }

    function acceptTurn(result) {
        if (result.turn_version >= turn.turn_version) turn = result;
        showTurn();
    }

    board.addEventListener("combatant:added", showTurn);
    board.addEventListener("character:updated", showTurn);

    board.addEventListener("combatants:cleared", (event) => {
        acceptTurn(event.detail);
    });

    board.addEventListener("combatant:removed", (event) => {
        acceptTurn(event.detail.turn);
    });

    async function saveTurn(url, body, method = "POST") {
        if (saving) return;
        saving = true;
        rollButton.disabled = true;
        nextButton.disabled = true;
        list.querySelectorAll("input").forEach((input) => { input.readOnly = true; });
        hint.textContent = "";
        try {
            const response = await fetch(url, {
                method,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify(body),
            });
            const result = await response.json();
            if (!response.ok) {
                if (response.status === 409 && result.rolls) acceptTurn(result);
                hint.textContent = result.error || "Couldn’t save the turn. Try again.";
                return;
            }
            acceptTurn(result);
        } catch {
            hint.textContent = "Couldn’t confirm the turn. Try again.";
        } finally {
            saving = false;
            showTurn();
        }
    }

    rollButton.addEventListener("click", () => {
        const cards = board.querySelectorAll(".combatant");
        if (!cards.length) {
            hint.textContent = "Add a combatant before rolling initiative.";
            return;
        }

        const rolls = {};
        for (const card of cards) rolls[card.dataset.id] = rollDice(20, 1).total;
        saveTurn(rollButton.dataset.url, { rolls });
    });

    nextButton.addEventListener("click", () => {
        saveTurn(nextButton.dataset.url, { turn_version: turn.turn_version });
    });

    showTurn();
}
