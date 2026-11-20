import { rollDice } from "./dice.js";

export function setupInitiativeRoller() {
    const board = document.getElementById("board");
    const rollButton = document.getElementById("initBtn");
    const nextButton = document.getElementById("nextBtn");
    const status = document.getElementById("turnInfo");
    const hint = document.getElementById("hint");
    let turn = JSON.parse(document.getElementById("initialTurn").textContent);

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

        nextButton.disabled = !activeCard;
        if (activeCard) {
            const name = activeCard.querySelector(".name").textContent;
            status.textContent = `Round ${turn.round} · ${name}’s turn`;
        } else if (turn.active_id !== null) {
            status.textContent = "Reload to see the current combatant.";
        } else {
            status.textContent = "Roll initiative to begin";
        }
    }

    board.addEventListener("combatants:cleared", (event) => {
        turn = event.detail;
        showTurn();
    });

    async function saveTurn(url, body) {
        rollButton.disabled = true;
        nextButton.disabled = true;
        hint.textContent = "";
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
                body: JSON.stringify(body),
            });
            const result = await response.json();
            if (!response.ok) {
                hint.textContent = result.error || "Couldn’t save the turn. Try again.";
                return;
            }
            turn = result;
        } catch {
            hint.textContent = "Couldn’t confirm the turn. Try again.";
        } finally {
            rollButton.disabled = false;
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
