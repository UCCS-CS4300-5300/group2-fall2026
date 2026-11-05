const addForm = document.getElementById("createForm");
const errorEl = document.getElementById("createError");

addForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // Avoid the default behavior
    errorEl.textContent = "";

    const submitBtn = addForm.querySelector('[type="submit"]')
    submitBtn.disabled = true;

    try {
        const res = await fetch(addForm.action, {
            method: "POST",
            body: new FormData(addForm),
            headers: {"X-Requested-With": "XMLHttpRequest"},
        })

        if (!res.ok) {
            errorEl.textContent = "Something went wrong.";
            return;
        }

        const html = await res.text()

        // success: add the new thing to the page
        document.getElementById("encounterGrid").insertAdjacentHTML("beforeend", html);

        bootstrap.Modal.getInstance(document.getElementById("createModal")).hide();
    }

    catch (err) {
        console.log(err)
        errorEl.textContent = "Network error. Try again.";
    }

    finally {
        addForm.reset();
        submitBtn.disabled = false;
    }
})