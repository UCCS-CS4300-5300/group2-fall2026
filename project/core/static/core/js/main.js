import { setupDraggableCharacterCard, savePositionOnMove } from "./drag.js";
import { setupDiceRoller } from "./dice.js";
import { setupQuests } from "./quests.js";
import { setupPreset } from "./enemy_presets.js";
import { setupSelectableCharacterCard } from "./character_select.js";
import { setupEditableHp } from "./editable_hp.js";

setupDraggableCharacterCard() //Make character cards draggable
setupSelectableCharacterCard() // Make character cards selectable
savePositionOnMove() //Make sure dragged cards position get saved
setupDiceRoller()
setupQuests()
setupPreset() 
setupEditableHp() // Make character current HP editable

//Logic for adding new combatant with the "addForm" element on the home template.
const addForm = document.getElementById("addForm");
const addModalEl = document.getElementById("addModal")
addForm.addEventListener("submit", async (e) => {
    e.preventDefault() //Prevent default submission behavior since this function handles the POST request

    // 
    const submitButton = addForm.querySelector (
        'button[type="submit"]'
    )

    // 
    if (submitButton) {
        submitButton.disabled = true;
    }

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

const chatHistories = new Map();

document.querySelectorAll(".chat-form").forEach((form) => {
    const messagesEl = document.getElementById(form.dataset.messages);
    const statusEl = document.getElementById(form.dataset.status);
    const input = form.elements.message;
    const sendButton = form.querySelector("button[type='submit']");
    chatHistories.set(form.dataset.chatType, []);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = input.value.trim();
        if (!message) {
            statusEl.textContent = "Enter a message before sending.";
            return;
        }
        if (message.length > input.maxLength) {
            statusEl.textContent = `Message must be at most ${input.maxLength} characters.`;
            return;
        }

        const userMessage = document.createElement("p");
        userMessage.className = "chat-message user-message";
        userMessage.textContent = `You: ${message}`;
        messagesEl.append(userMessage);
        statusEl.classList.remove("text-danger");
        statusEl.textContent = "Thinking...";
        input.disabled = true;
        sendButton.disabled = true;

        const formData = new FormData(form);
        formData.set("message", message);
        formData.set("chat_type", form.dataset.chatType);
        formData.set("history", JSON.stringify(chatHistories.get(form.dataset.chatType)));

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "The chat request failed.");

            const assistantMessage = document.createElement("p");
            assistantMessage.className = "chat-message assistant-message";
            assistantMessage.textContent = result.reply;
            messagesEl.append(assistantMessage);
            const history = chatHistories.get(form.dataset.chatType);
            history.push(
                { role: "user", content: message },
                { role: "assistant", content: result.reply },
            );
            if (history.length > 20) history.splice(0, history.length - 20);
            input.value = "";
            statusEl.textContent = "";
        } catch (error) {
            statusEl.textContent = error.message || "Could not reach the chat service.";
            statusEl.classList.add("text-danger");
        } finally {
            input.disabled = false;
            sendButton.disabled = false;
            input.focus();
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    });
});
