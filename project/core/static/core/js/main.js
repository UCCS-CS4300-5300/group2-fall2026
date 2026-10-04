//Function to allow combatant cards to be draggable
(function () {
    const board = document.getElementById("board");
    if (!board) return;

    let active = null; // { el, offsetX, offsetY }

    board.addEventListener("pointerdown", (e) => {
        // Only primary button for mouse; ignore clicks on interactive children
        if (e.button !== undefined && e.button !== 0) return;
        if (e.target.closest("button, input, select, a")) return;

        const card = e.target.closest(".combatant");
        if (!card) return;

        // Card position relative to the board's scrollable content area
        const boardRect = board.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();

        active = {
            el: card,
            // Where inside the card the pointer grabbed, so it doesn't jump
            offsetX: e.clientX - cardRect.left,
            offsetY: e.clientY - cardRect.top,
            moved: false,
            startX: e.clientX,
            startY: e.clientY,
        };

        card.setPointerCapture(e.pointerId);
        card.classList.add("dragging");
        e.preventDefault();
    });

    board.addEventListener("pointermove", (e) => {
        if (!active) return;

        // Small threshold so a plain click isn't treated as a drag
        if (!active.moved) {
            const dx = e.clientX - active.startX;
            const dy = e.clientY - active.startY;
            if (Math.hypot(dx, dy) < 3) return;
            active.moved = true;
        }

        const boardRect = board.getBoundingClientRect();
        const card = active.el;

        // Convert pointer position into board content coordinates (accounts for scroll)
        let x = e.clientX - boardRect.left + board.scrollLeft - active.offsetX;
        let y = e.clientY - boardRect.top + board.scrollTop - active.offsetY;

        // Keep the card from going above/left of the board
        x = Math.max(0, x);
        y = Math.max(0, y);

        card.style.left = x + "px";
        card.style.top = y + "px";
    });

    function endDrag(e) {
        if (!active) return;
        const card = active.el;
        card.classList.remove("dragging");
        if (card.hasPointerCapture(e.pointerId)) {
            card.releasePointerCapture(e.pointerId);
        }

        if (active.moved) {
            // Swallow the click that follows a drag so it doesn't select/target the card
            card.addEventListener("click", (ev) => ev.stopPropagation(), {
                once: true,
                capture: true,
            });

            card.dispatchEvent(
                new CustomEvent("combatant:moved", {
                    bubbles: true,
                    detail: {
                        x: parseInt(card.style.left, 10),
                        y: parseInt(card.style.top, 10),
                    },
                }),
            );
        }
        active = null;
    }

    board.addEventListener("pointerup", endDrag);
    board.addEventListener("pointercancel", endDrag);
})();
