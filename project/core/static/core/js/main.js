import { draggableCharacterCard } from "./drag.js";
draggableCharacterCard() //Make character cards draggable

//Logic for adding new combatant with the "addForm" element on the home template.
const addForm = document.getElementById("addForm");
const addModalEl = document.getElementById("addModal")
addForm.addEventListener("submit", async (e) => {
    e.preventDefault() //Prevent default submission behavior since this function handles the POST request

    //Send POST request to add a new combatant, and render the card on screen.
    const res = await fetch(addForm.action || window.location.href, {
        method: "POST",
        body: new FormData(addForm), // includes the csrfmiddlewaretoken field
        headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    //Check if response is okay
    if (!res.ok) {
        //TODO: Add error checking!!!
        return
    }

    //Add returned HTML fragment to page
    const html = await res.text()
    document.getElementById("board").insertAdjacentHTML("beforeend", html)
    
    const emptyMsgEl = document.getElementById("emptyMsg");
    if (emptyMsgEl) emptyMsgEl.style.display = "none";

    addForm.reset()
    bootstrap.Modal.getOrCreateInstance(addModalEl).hide();
})