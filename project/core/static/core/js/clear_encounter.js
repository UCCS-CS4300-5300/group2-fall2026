export function setupClearEncounter() {
    const button = document.getElementById("resetBtn");
    const board = document.getElementById("board");
    if (!button || !board) return;

    const hint = document.getElementById("hint");

    button.addEventListener("click", async () => {
        if (!window.confirm("Remove all combatants? NPCs, quests, and the log will be kept.")) {
            return;
        }

        button.disabled = true;
        hint.textContent = "";
        try {
            const token = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
            if (!token) throw new Error("Could not find the request security token.");

            const response = await fetch(button.dataset.url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": token,
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `Could not clear combatants (HTTP ${response.status}).`);
            }

            board.querySelectorAll(".combatant").forEach((card) => card.remove());
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
            board.dispatchEvent(new CustomEvent("combatants:cleared", { detail: result }));
        } catch (error) {
            hint.textContent = error.message || "Could not clear combatants. Try again.";
        } finally {
            button.disabled = false;
        }
    });
}
