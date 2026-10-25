export function setupQuests() {
    const form = document.getElementById("questForm");
    if (!form) return;

    const list = document.getElementById("quests");
    const empty = document.getElementById("questEmpty");
    const error = document.getElementById("questError");
    const input = document.getElementById("questInput");
    const addButton = form.querySelector("button[type=submit]");
    const token = form.elements.namedItem("csrfmiddlewaretoken").value;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (addButton.disabled) return;
        error.textContent = "";
        addButton.disabled = true;
        const data = new FormData(form);
        input.disabled = true;

        try {
            const response = await fetch(form.action, { method: "POST", body: data });
            if (response.status === 400) {
                const errors = await response.json();
                error.textContent = Object.values(errors).flat().join(" ");
                return;
            }
            if (!response.ok) throw new Error("Could not save quest");

            // The template escapes the note before it gets added to the list.
            list.insertAdjacentHTML("beforeend", await response.text());
            empty.hidden = true;
            form.reset();
        } catch {
            error.textContent = "Couldn't save the quest. Your text is still here; try again.";
        } finally {
            input.disabled = false;
            addButton.disabled = false;
        }
    });

    list.addEventListener("change", async (event) => {
        const checkbox = event.target;
        if (!checkbox.matches("input[type=checkbox]")) return;
        const item = checkbox.closest("li");
        const deleteButton = item.querySelector("button");
        const completed = checkbox.checked;
        checkbox.disabled = true;
        deleteButton.disabled = true;
        error.textContent = "";

        try {
            const response = await fetch(item.dataset.url, {
                method: "PATCH",
                headers: { "Content-Type": "application/json", "X-CSRFToken": token },
                body: JSON.stringify({ completed }),
            });
            if (!response.ok) throw new Error("Could not update quest");
            const saved = await response.json();
            checkbox.checked = saved.completed;
            const label = item.querySelector("label");
            label.classList.toggle("text-decoration-line-through", saved.completed);
            label.classList.toggle("text-secondary", saved.completed);
        } catch {
            checkbox.checked = !completed;
            error.textContent = "Couldn't update the quest. Try again.";
        } finally {
            checkbox.disabled = false;
            deleteButton.disabled = false;
        }
    });

    list.addEventListener("click", async (event) => {
        const button = event.target.closest("button");
        if (!button || button.disabled) return;
        const item = button.closest("li");
        const checkbox = item.querySelector("input");
        button.disabled = true;
        checkbox.disabled = true;
        error.textContent = "";

        try {
            const response = await fetch(item.dataset.url, {
                method: "DELETE",
                headers: { "X-CSRFToken": token },
            });
            if (!response.ok) throw new Error("Could not delete quest");
            item.remove();
            empty.hidden = list.children.length > 0;
        } catch {
            error.textContent = "Couldn't delete the quest. Try again.";
        } finally {
            button.disabled = false;
            checkbox.disabled = false;
        }
    });
}
