export function setupRemoveCombatant() {
    const board = document.getElementById("board");
    if (!board) return;

    const hint = document.getElementById("hint");

    board.addEventListener("click", async (event) => {
        const button = event.target.closest(".combatant-remove");
        if (!button || !board.contains(button) || button.disabled) return;

        const card = button.closest(".combatant");
        button.disabled = true;
        hint.textContent = "";

        try {
            const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
            if (!token) throw new Error("Could not find the request security token.");

            const response = await fetch(card.dataset.removeUrl, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": token,
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            if (!response.ok) {
                throw new Error(`Could not remove combatant (HTTP ${response.status}).`);
            }

            const turn = await response.json();
            const id = card.dataset.id;
            card.remove();

            if (!board.querySelector(".combatant")) {
                let emptyMessage = document.getElementById("emptyMsg");
                if (!emptyMessage) {
                    emptyMessage = document.createElement("div");
                    emptyMessage.id = "emptyMsg";
                    emptyMessage.className = "position-absolute top-50 start-50 translate-middle text-secondary text-center";
                    const title = document.createElement("p");
                    title.className = "mb-1";
                    title.textContent = "No combatants yet.";
                    const instructions = document.createElement("p");
                    instructions.className = "small";
                    instructions.textContent = 'Use "Add combatant" below to create players and enemies.';
                    emptyMessage.append(title, instructions);
                    board.append(emptyMessage);
                } else {
                    emptyMessage.style.display = "";
                }
            }

            board.dispatchEvent(
                new CustomEvent("combatant:removed", { detail: { id, turn } }),
            );
        } catch (error) {
            hint.textContent = error.message || "Could not remove combatant. Try again.";
        } finally {
            if (button.isConnected) button.disabled = false;
        }
    });
}
