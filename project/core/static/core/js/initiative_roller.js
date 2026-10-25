import { rollDice } from "./dice.js";

//Add listener for "Roll initiative" button
export function setupInitiativeRoller() {
    const initBtn = document.getElementById("initBtn");
    initBtn.addEventListener('click', () => {
        const charCards = document.querySelectorAll(".combatant");
        // Do this for each character card
        for (const card of charCards) {
            const badge = card.querySelector(".init-badge");
            if (!badge) continue;
            
            const initiative = rollDice(20, 1).total;
            const originalVisibility = badge.style.visibility;
            const originalInitiative = badge.textContent;

            badge.style.visibility="visible";
            badge.textContent=initiative;

            // If we have an error log it and revert initiative badge to original state
            const onError = (errStr, status) => {
                console.error(`Returned ${status}\n${errStr}`);
                badge.style.visibility=originalVisibility;
                badge.textContent=originalInitiative;
            }

            // If the return value isn't the same as the sent value, use the actual value for consistency with backend
            const onMismatchedReturnValue = (actualInitiative) => {
                console.log(actualInitiative)
                badge.textContent = actualInitiative;
            }

            // Send request to update initiative
            // Right now this sends a new request for each character, but if this is a problem we can maybe batch this?
            patchInitiativeReq(card, initiative, onError, onMismatchedReturnValue);
        }
    })
}

// Sends PATCH request to backend to update the character's initiative
// onError should take (error->str, status code->int)
// onMismatchedReturnValue should take the actual returned value
async function patchInitiativeReq(combatant, newInitiative, onError, onMismatchedReturnValue) {
    const token = document.querySelector("[name=csrfmiddlewaretoken]").value;

    let res;
    try {
        res = await fetch(combatant.dataset.updateInitiativeUrl, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": token,
            },
            body: JSON.stringify({ initiative: newInitiative }),
        });
    } catch (err) {
        // Only genuine network failures end up here
        onError("Could not reach server: " + String(err), null);
        return;
    }

    if (!res.ok) {
        let errStr = "Unknown error.";
        try {
            const data = await res.json();
            errStr = data.error ?? errStr;
        } catch {}
        onError("Unable to update initiative: " + errStr, res.status);
        return;
    }

    let data;
    try {
        data = await res.json();
    } catch {
        onError("Server returned an invalid response.", res.status);
        return;
    }

    if (data.initiative !== Number(newInitiative)) {
        onMismatchedReturnValue(data.initiative);
    }
}