import test from "node:test";
import assert from "node:assert/strict";
import {
    enforceExclusiveTraitSelection,
    resolveDefendOutcome,
    rollSavingThrowD20,
} from "../core/static/core/js/defend.js";

test("damage traits are mutually exclusive", () => {
    const checkboxes = new Map([
        ["resistant", { checked: true }],
        ["immune", { checked: true }],
        ["vulnerable", { checked: true }],
        ["advantage", { checked: true }],
        ["disadvantage", { checked: true }],
    ]);

    enforceExclusiveTraitSelection("immune", checkboxes);
    assert.deepEqual(
        ["resistant", "immune", "vulnerable"].map((trait) => checkboxes.get(trait).checked),
        [false, true, false],
    );
    assert.equal(checkboxes.get("advantage").checked, true);
    assert.equal(checkboxes.get("disadvantage").checked, true);

    enforceExclusiveTraitSelection("disadvantage", checkboxes);
    assert.equal(checkboxes.get("advantage").checked, false);
    assert.equal(checkboxes.get("disadvantage").checked, true);
});

test("advantage and disadvantage select the higher and lower of two rolls", (t) => {
    const random = [0.2, 0.7, 0.8, 0.2];
    const mock = t.mock.method(Math, "random", () => random.shift());

    assert.deepEqual(rollSavingThrowD20(true, false), {
        rolls: [5, 15],
        selected: 15,
    });
    assert.deepEqual(rollSavingThrowD20(false, true), {
        rolls: [17, 5],
        selected: 5,
    });
    assert.equal(mock.mock.callCount(), 4);
});

test("ordinary saves roll once and advantage cancels disadvantage", (t) => {
    const random = [0.4, 0.6];
    const mock = t.mock.method(Math, "random", () => random.shift());

    assert.deepEqual(rollSavingThrowD20(false, false), {
        rolls: [9],
        selected: 9,
    });
    assert.deepEqual(rollSavingThrowD20(true, true), {
        rolls: [13],
        selected: 13,
    });
    assert.equal(mock.mock.callCount(), 2);
});

function outcome(overrides = {}) {
    return resolveDefendOutcome({
        damage: 20,
        mode: "attack",
        attackRoll: 16,
        armorClass: 15,
        saveTotal: null,
        dc: 15,
        halfOnSave: false,
        traits: new Set(),
        ...overrides,
    });
}

test("attack misses do not apply damage", () => {
    assert.deepEqual(outcome({ attackRoll: 15 }), {
        missed: true,
        amount: 0,
        saved: null,
    });
});

test("saving throw success, half damage, and failure produce the expected damage", () => {
    assert.deepEqual(outcome({ mode: "save", saveTotal: 15, dc: 15 }), {
        missed: false,
        amount: 0,
        saved: true,
    });
    assert.equal(outcome({
        mode: "save",
        saveTotal: 15,
        dc: 15,
        halfOnSave: true,
    }).amount, 10);
    assert.deepEqual(outcome({ mode: "save", saveTotal: 14, dc: 15 }), {
        missed: false,
        amount: 20,
        saved: false,
    });
});

test("immunity, resistance, and vulnerability modify damage as expected", () => {
    assert.equal(outcome({ traits: new Set(["immune"]) }).amount, 0);
    assert.equal(outcome({ traits: new Set(["resistant"]) }).amount, 10);
    assert.equal(outcome({ traits: new Set(["resistant"]), damage: 1 }).amount, 1);
    assert.equal(outcome({ traits: new Set(["vulnerable"]) }).amount, 40);
});
