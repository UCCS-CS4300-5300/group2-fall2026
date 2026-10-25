import { rollDice } from "./dice.js";

//Add listener for "Roll initiative" button
export function setupInitiativeRoller() {
    const initBtn = document.getElementById("initBtn");
    const charCards = document.getElementsByClassName("combatant");
    initBtn.addEventListener('click', (e) => {
        // Do this for each character card
        for (let i = 0; i < charCards.length; i++) {
            const card = charCards[i]
            const initBadge = card.getElementsByClassName("init-badge");
            if (!initBadge) return;
            
            const badge = initBadge[0]
            const initiative = rollDice(20, 1).total
            badge.style.visibility="visible"
            badge.innerHTML=initiative
        }
    })
}

// TODO: Implement
function patchInitiativeReq() {}