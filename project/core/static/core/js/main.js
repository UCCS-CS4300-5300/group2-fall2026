import { setupDraggableCharacterCard, savePositionOnMove } from "./drag.js";
import { setupDiceRoller } from "./dice.js";
import { setupQuests } from "./quests.js";
import { setupPanelResize } from "./panel_resize.js";
import { setupPreset } from "./enemy_presets.js";
import { setupSelectableCharacterCard } from "./character_select.js";
import { setupEditableHp } from "./editable_hp.js";
import { setupEditableCharacterFields } from "./editable_character.js";
import { setupInitiativeRoller } from "./initiative_roller.js";
import { setupDefend } from "./defend.js";
import { setupSavingThrowRoller } from "./saving_throws.js";
import { setupClearEncounter } from "./clear_encounter.js";
import { setupRemoveCombatant } from "./remove_combatant.js";

setupDraggableCharacterCard() //Make character cards draggable
setupSelectableCharacterCard() // Make character cards selectable
savePositionOnMove() //Make sure dragged cards position get saved
setupDiceRoller()
setupQuests()
setupPanelResize()
setupPreset() 
setupEditableHp() // Make character current HP editable
setupEditableCharacterFields()
setupInitiativeRoller()
setupClearEncounter()
setupRemoveCombatant()
setupDefend()
setupSavingThrowRoller()

//Logic for adding new combatant with the "addForm" element on the home template.
const addForm = document.getElementById("addForm");
const addModalEl = document.getElementById("addModal")
addForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitButton = addForm.querySelector('button[type="submit"]');
    if (submitButton.disabled) return;
    submitButton.disabled = true;
    const error = document.getElementById("addCombatantError");
    error.textContent = "";

    try {
        const res = await fetch(addForm.action || window.location.href, {
            method: "POST",
            body: new FormData(addForm),
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!res.ok) throw new Error("Could not add combatant. Check the fields and try again.");

        const html = await res.text();
        const board = document.getElementById("board");
        board.insertAdjacentHTML("beforeend", html);
        board.dispatchEvent(new CustomEvent("combatant:added"));
        const emptyMsgEl = document.getElementById("emptyMsg");
        if (emptyMsgEl) emptyMsgEl.style.display = "none";

        addForm.reset();
        bootstrap.Modal.getOrCreateInstance(addModalEl).hide();
    } catch (failure) {
        error.textContent = failure.message || "Could not add combatant. Try again.";
    } finally {
        submitButton.disabled = false;
    }
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

            const assistantMessage = document.createElement("div");
            assistantMessage.className = "chat-message assistant-message";
            assistantMessage.innerHTML = DOMPurify.sanitize(marked.parse(result.reply, { breaks: true }));
            messagesEl.append(assistantMessage);
            const history = chatHistories.get(form.dataset.chatType);
            history.push(
                { role: "user", content: message },
                { role: "assistant", content: result.reply },
            );
            // Hard caps history length to 20. I want to say this should be changed in case different models 
            // can handle different history sizes, but this is fine for now as like a max-limit.
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
