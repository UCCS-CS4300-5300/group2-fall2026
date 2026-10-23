// Click a combatant card to select it (one selected at a time)
export function selectableCharacterCard() {
    const board = document.getElementById("board");
    if (!board) return;

    board.addEventListener("click", (e) => {
        // Ignore clicks on interactive children
        if (e.target.closest("button, input, select, a")) return;

        const card = e.target.closest(".combatant");

        // Clicking empty board space deselects
        if (!card) {
            clearSelection();
            return;
        }

        const alreadySelected = card.classList.contains("selected");
        clearSelection();

        if (!alreadySelected) {
            card.classList.add("selected");
            card.dispatchEvent(
                new CustomEvent("combatant:selected", {
                    bubbles: true,
                    detail: { id: card.dataset.id },
                }),
            );
        }
    });

    function clearSelection() {
        board
            .querySelectorAll(".combatant.selected")
            .forEach((el) => el.classList.remove("selected"));
    }
}