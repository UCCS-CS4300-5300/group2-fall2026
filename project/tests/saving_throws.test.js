import test from "node:test";
import assert from "node:assert/strict";
import {
    calculateSavingThrow,
    getSavingThrowBonus,
    rollSavingThrow,
} from "../core/static/core/js/saving_throws.js";

test("reads the matching saved bonus for each ability", () => {
    const combatant = {
        dataset: {
            saveStrengthBonus: "1",
            saveDexterityBonus: "2",
            saveConstitutionBonus: "3",
            saveIntelligenceBonus: "4",
            saveWisdomBonus: "5",
            saveCharismaBonus: "-6",
        },
    };

    assert.deepEqual(
        ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
            .map((ability) => getSavingThrowBonus(combatant, ability)),
        [1, 2, 3, 4, 5, -6],
    );
});

test("adds the saved bonus and succeeds when the total meets the DC", () => {
    const random = [0.5];
    const combatant = { dataset: { saveWisdomBonus: "4" } };
    const mock = test.mock.method(Math, "random", () => random.shift());

    assert.deepEqual(rollSavingThrow(combatant, "wisdom", 15), {
        die: 11,
        bonus: 4,
        dc: 15,
        total: 15,
        success: true,
    });
    assert.equal(mock.mock.callCount(), 1);
});

test("negative bonuses are included and a total below DC fails", (t) => {
    t.mock.method(Math, "random", () => 0.4);
    const combatant = { dataset: { saveDexterityBonus: "-2" } };

    assert.deepEqual(rollSavingThrow(combatant, "dexterity", 10), {
        die: 9,
        bonus: -2,
        dc: 10,
        total: 7,
        success: false,
    });
});

test("ordinary saves compare totals without natural-1 or natural-20 overrides", (t) => {
    const rolls = [0, 0.999999];
    t.mock.method(Math, "random", () => rolls.shift());
    const combatant = { dataset: { saveStrengthBonus: "10" } };

    assert.equal(rollSavingThrow(combatant, "strength", 11).success, true);
    combatant.dataset.saveStrengthBonus = "0";
    assert.equal(rollSavingThrow(combatant, "strength", 21).success, false);
});

test("rejects invalid abilities, bonuses, DCs, and die results", (t) => {
    const random = t.mock.method(Math, "random");
    assert.throws(
        () => rollSavingThrow({ dataset: {} }, "luck", 10),
        /valid saving throw ability/,
    );
    assert.throws(
        () => rollSavingThrow({ dataset: { saveStrengthBonus: "bad" } }, "strength", 10),
        /invalid saving throw bonus/,
    );
    assert.throws(
        () => rollSavingThrow({ dataset: { saveStrengthBonus: "0" } }, "strength", 0),
        /positive whole number/,
    );
    assert.throws(() => calculateSavingThrow(0, 0, 10), /d20 result/);
    assert.throws(() => calculateSavingThrow(10, 0.5, 10), /bonus must be an integer/);
    assert.equal(random.mock.callCount(), 0);
});