const MIN_TOOLS_WIDTH = 300;
const MIN_BOARD_WIDTH = 360;

export function clampToolsWidth(width, availableWidth) {
    const maximum = Math.max(MIN_TOOLS_WIDTH, availableWidth - MIN_BOARD_WIDTH);
    return Math.min(Math.max(width, MIN_TOOLS_WIDTH), maximum);
}

export function setupPanelResize() {
    const divider = document.getElementById("panelDivider");
    if (!divider) return;

    const layout = divider.parentElement;
    const tools = document.getElementById("toolsPanel");
    const narrow = window.matchMedia("(max-width: 800px)");
    let toolsWidth = narrow.matches ? 340 : tools.getBoundingClientRect().width;
    let drag = null;

    function resize(width) {
        if (narrow.matches) return;
        const available = layout.clientWidth - divider.offsetWidth;
        toolsWidth = clampToolsWidth(width, available);
        layout.style.setProperty("--tools-width", `${toolsWidth}px`);
        divider.setAttribute("aria-valuemin", MIN_TOOLS_WIDTH);
        divider.setAttribute("aria-valuemax", Math.max(MIN_TOOLS_WIDTH, available - MIN_BOARD_WIDTH));
        divider.setAttribute("aria-valuenow", Math.round(toolsWidth));
        divider.setAttribute("aria-valuetext", `Tools panel ${Math.round(toolsWidth)} pixels wide`);
    }

    function stopDrag() {
        if (!drag) return;
        const pointerId = drag.pointerId;
        drag = null;
        layout.classList.remove("resizing");
        if (divider.hasPointerCapture(pointerId)) divider.releasePointerCapture(pointerId);
    }

    divider.addEventListener("pointerdown", (event) => {
        if (narrow.matches || event.button !== 0 || drag) return;
        drag = { pointerId: event.pointerId, startX: event.clientX, width: toolsWidth };
        divider.setPointerCapture(event.pointerId);
        divider.focus();
        layout.classList.add("resizing");
        event.preventDefault();
    });

    divider.addEventListener("pointermove", (event) => {
        if (!drag || event.pointerId !== drag.pointerId) return;
        resize(drag.width + drag.startX - event.clientX);
    });

    for (const type of ["pointerup", "pointercancel", "lostpointercapture"]) {
        divider.addEventListener(type, (event) => {
            if (drag?.pointerId === event.pointerId) stopDrag();
        });
    }

    divider.addEventListener("keydown", (event) => {
        const available = layout.clientWidth - divider.offsetWidth;
        let width = toolsWidth;
        if (event.key === "ArrowLeft") width += 20;
        else if (event.key === "ArrowRight") width -= 20;
        else if (event.key === "Home") width = MIN_TOOLS_WIDTH;
        else if (event.key === "End") width = available - MIN_BOARD_WIDTH;
        else return;
        event.preventDefault();
        resize(width);
    });

    window.addEventListener("resize", () => {
        stopDrag();
        resize(toolsWidth);
    });
    resize(toolsWidth);
}
