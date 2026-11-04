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