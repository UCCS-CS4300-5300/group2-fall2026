const addForm = document.getElementById("createForm");
const createErrorEl = document.getElementById("createError");

const delForm = document.getElementById("deleteForm");
const delModal = document.getElementById("deleteModal")
const delErrorEl = document.getElementById("deleteError")


addForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // Avoid the default behavior
    createErrorEl.textContent = "";

    const submitBtn = addForm.querySelector('[type="submit"]')
    submitBtn.disabled = true;

    try {
        const res = await fetch(addForm.action, {
            method: "POST",
            body: new FormData(addForm),
            headers: {"X-Requested-With": "XMLHttpRequest"},
        })

        if (!res.ok) {
            createErrorEl.textContent = "Something went wrong.";
            return;
        }

        const html = await res.text()

        // success: add the new thing to the page
        document.getElementById("encounterGrid").insertAdjacentHTML("beforeend", html);

        //Turn off the "First Encounter" text if exists
        const firstEncounterMessage = document.getElementById("emptyMsg");
        if (firstEncounterMessage) {
            firstEncounterMessage.style.display = "none";
        }

        bootstrap.Modal.getInstance(document.getElementById("createModal")).hide();
    }

    catch (err) {
        console.log(err)
        createErrorEl.textContent = "Network error. Try again.";
    }

    finally {
        addForm.reset();
        submitBtn.disabled = false;
    }
})

// When delete modal opens up, fill in information and also the form submit action
delModal.addEventListener("show.bs.modal", (e) => {
    const button = e.relatedTarget; // Delete button
    const name = button.dataset.name;
    const url = button.dataset.deleteUrl;
    const id = button.dataset.id;    

    const encounterNameEl = document.getElementById("deleteEncounterName");
    encounterNameEl.textContent = name;
    
    delForm.action = url;
    delForm.dataset.encounterId = id 
})

delForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // Avoid the default behavior
    delErrorEl.textContent = "";

    const submitBtn = delForm.querySelector('[type="submit"]')
    submitBtn.disabled = true;

    const token = document.querySelector("[name=csrfmiddlewaretoken]").value;
    try {
        const res = await fetch(delForm.action, {
            method: "DELETE",
            body: new FormData(delForm),
            headers: {'X-CSRFToken': token},
        })

        if (!res.ok) {
            console.log("Something went wrong.")
            delErrorEl.textContent = "Network error. Try again.";
            return;
        }

        // success: remove the card from the DOM
        var card = document.getElementById(`encounter-${delForm.dataset.encounterId}`)
        card.remove()
        bootstrap.Modal.getInstance(document.getElementById("deleteModal")).hide();
    }

    catch (err) {
        console.log(err)
        delErrorEl.textContent = "Network error. Try again.";
    }

    finally {
        delForm.reset();
        submitBtn.disabled = false;
    }
})