import { draggableCharacterCard } from "./drag.js";
draggableCharacterCard() //Make character cards draggable

//Logic for adding new combatant with the "addForm" element on the home template.
const addForm = document.getElementById("addForm");
addForm.addEventListener("submit", async (e) => {
    e.preventDefault() //Prevent default submission behavior since this function handles the POST request
})