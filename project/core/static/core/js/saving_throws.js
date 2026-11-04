import { rollDice } from "./dice.js";

const SAVE_BONUS_DATA_KEYS = {
    strength: "saveStrengthBonus",
    dexterity: "saveDexterityBonus",
    constitution: "saveConstitutionBonus",
    intelligence: "saveIntelligenceBonus",
    wisdom: "saveWisdomBonus",
    charisma: "saveCharismaBonus",
};

export function getSavingThrowBonus(combatant, ability) {
    const dataKey = SAVE_BONUS_DATA_KEYS[ability];
    if (!dataKey) throw new Error("Choose a valid saving throw ability.");

    const rawBonus = combatant?.dataset?.[dataKey];
    if (typeof rawBonus !== "string" || rawBonus.trim() === "") {
        throw new Error("The selected combatant has no bonus for that ability.");
    }

    const bonus = Number(rawBonus);
    if (!Number.isSafeInteger(bonus)) {
        throw new Error("The selected combatant has an invalid saving throw bonus.");
    }
    return bonus;
}

export function calculateSavingThrow(die, bonus, dc) {
    if (!Number.isInteger(die) || die < 1 || die > 20) {
        throw new Error("A saving throw requires a d20 result from 1 to 20.");
    }
    if (!Number.isSafeInteger(bonus)) {
        throw new Error("The saving throw bonus must be an integer.");
    }
    if (!Number.isSafeInteger(dc) || dc < 1) {
        throw new Error("The difficulty class must be a positive whole number.");
    }

    const total = die + bonus;
    return { die, bonus, dc, total, success: total >= dc };
}

export function rollSavingThrow(combatant, ability, dc) {
    if (!Number.isSafeInteger(dc) || dc < 1) {
        throw new Error("The difficulty class must be a positive whole number.");
    }

    const bonus = getSavingThrowBonus(combatant, ability);
    const die = rollDice(20, 1).total;
    return calculateSavingThrow(die, bonus, dc);
}

export function setupSavingThrowRoller() {
    const form = document.getElementById("savingThrowForm");
    const board = document.getElementById("board");
    if (!form || !board) return;

    const selectedTarget = document.getElementById("savingThrowTarget");
    const result = document.getElementById("savingThrowResult");
    const error = document.getElementById("savingThrowError");
    const log = document.getElementById("log");
    const abilityLabels = {
        strength: "Strength",
        dexterity: "Dexterity",
        constitution: "Constitution",
        intelligence: "Intelligence",
        wisdom: "Wisdom",
        charisma: "Charisma",
    };
    let selectedCombatant = null;

    board.addEventListener("combatant:selected", (event) => {
        selectedCombatant = event.target.closest(".combatant");
        const name = selectedCombatant.querySelector(".name")?.textContent.trim();
        selectedTarget.textContent = `Selected: ${name || "Combatant"}`;
        result.textContent = "";
        error.textContent = "";
    });

    board.addEventListener("combatant:deselected", (event) => {
        if (event.target !== selectedCombatant) return;
        selectedCombatant = null;
        selectedTarget.textContent = "No combatant selected";
        result.textContent = "";
        error.textContent = "";
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        result.textContent = "";
        error.textContent = "";

        try {
            if (!selectedCombatant) {
                throw new Error("Select a combatant card before rolling.");
            }

            const ability = form.elements.namedItem("ability").value;
            const dc = Number(form.elements.namedItem("dc").value);
            const savingThrow = rollSavingThrow(selectedCombatant, ability, dc);
            const name = selectedCombatant.querySelector(".name")?.textContent.trim();
            const modifier = savingThrow.bonus < 0
                ? `- ${Math.abs(savingThrow.bonus)}`
                : `+ ${savingThrow.bonus}`;
            const message = `${name || "Combatant"} ${abilityLabels[ability]} save: d20 ${savingThrow.die} ${modifier} = ${savingThrow.total} vs DC ${savingThrow.dc} (${savingThrow.success ? "Success" : "Failure"})`;
            result.textContent = message;

            const entry = document.createElement("p");
            entry.className = "small mb-2";
            entry.textContent = message;
            log.prepend(entry);
        } catch (rollError) {
            error.textContent = rollError.message;
        }
    });
}