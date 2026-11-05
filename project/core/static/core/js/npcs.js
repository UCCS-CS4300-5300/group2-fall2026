const tab = document.getElementById("npcTab");

if (tab) {
    const addForm = document.getElementById("npcForm");
    const list = document.getElementById("npcList");
    const empty = document.getElementById("npcEmpty");
    const status = document.getElementById("npcStatus");
    const retry = document.getElementById("npcRetry");

    async function loadNPCs() {
        retry.hidden = true;
        status.textContent = "Loading NPCs...";
        try {
            const response = await fetch(tab.dataset.listUrl);
            if (!response.ok) throw new Error("Could not load NPCs");
            list.innerHTML = await response.text();
            empty.hidden = list.children.length > 0;
            addForm.querySelector("fieldset").disabled = false;
            status.textContent = "";
        } catch {
            status.textContent = "Couldn't load NPCs. Try again.";
            retry.hidden = false;
        }
    }

    retry.addEventListener("click", loadNPCs);
    loadNPCs();

    tab.addEventListener("submit", async (event) => {
        event.preventDefault();
        const form = event.target;
        const fields = form.querySelector("fieldset");
        if (fields.disabled) return;
        const error = form.querySelector(".npc-error");
        const data = new FormData(form);
        fields.disabled = true;
        error.textContent = "";
        status.textContent = "";

        try {
            const response = await fetch(form.action, { method: "POST", body: data });
            if (response.status === 400) {
                const errors = await response.json();
                error.textContent = Object.values(errors).flat().join(" ");
                return;
            }
            if (!response.ok) throw new Error("Could not save NPC");
            const html = await response.text();
            if (form === addForm) {
                list.insertAdjacentHTML("beforeend", html);
                form.reset();
                empty.hidden = true;
            } else {
                form.closest(".npc-item").outerHTML = html;
            }
            status.textContent = "NPC saved.";
        } catch {
            error.textContent = "Couldn't save the NPC. Your text is still here; try again.";
        } finally {
            fields.disabled = false;
        }
    });

    tab.addEventListener("click", async (event) => {
        const button = event.target.closest(".npc-delete");
        if (!button) return;
        const form = button.closest("form");
        const fields = form.querySelector("fieldset");
        if (fields.disabled) return;
        const error = form.querySelector(".npc-error");
        fields.disabled = true;
        error.textContent = "";
        status.textContent = "";

        try {
            const response = await fetch(form.action, {
                method: "DELETE",
                headers: { "X-CSRFToken": form.elements.namedItem("csrfmiddlewaretoken").value },
            });
            if (!response.ok) throw new Error("Could not delete NPC");
            form.closest(".npc-item").remove();
            empty.hidden = list.children.length > 0;
            status.textContent = "NPC deleted.";
        } catch {
            error.textContent = "Couldn't delete the NPC. Try again.";
        } finally {
            fields.disabled = false;
        }
    });
}
