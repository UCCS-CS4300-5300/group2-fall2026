import test from "node:test";
import assert from "node:assert/strict";
import {
    formatAttackResult,
    rollAttack,
    splitAttackCount,
} from "../core/static/core/js/attacks.js";

test("rolls attack bonus and sums each damage component", (t) => {
    const values = [0.5, 0, 0.999999, 0.25];
    t.mock.method(Math, "random", () => values.shift());

    assert.deepEqual(rollAttack({
        attack_bonus: 9,
        dc: null,
        dc_type: "",
        dc_success: "",
        damage_components: [
            { damage_dice: "2d6", damage_modifier: 4, damage_type: "Fire" },
            { damage_dice: "1d4", damage_modifier: -1, damage_type: "Cold" },
        ],
    }), {
        attackRoll: { rolls: [11], selectedIndex: 0, die: 11, bonus: 9, total: 20 },
        dc: null,
        dcType: "",
        dcSuccess: "",
        damageComponents: [
            { dice: "2d6", rolls: [1, 6], modifier: 4, damage_type: "Fire", total: 11 },
            { dice: "1d4", rolls: [2], modifier: -1, damage_type: "Cold", total: 1 },
        ],
        damageTotal: 12,
    });
});

test("keeps save-based actions as a DC and rolls their damage", (t) => {
    t.mock.method(Math, "random", () => 0.5);

    const result = rollAttack({
        attack_bonus: null,
        dc: 15,
        dc_type: "DEX",
        dc_success: "half",
        damage_components: [
            { damage_dice: "1d8", damage_modifier: 0, damage_type: "Fire" },
        ],
    });

    assert.equal(result.attackRoll, null);
    assert.equal(result.dc, 15);
    assert.equal(result.damageTotal, 5);
    assert.equal(
        formatAttackResult(result)[0].text,
        "Save DC 15 DEX; half damage on save",
    );
    assert.deepEqual(formatAttackResult(result)[1], {
        prefix: "Damage: 1d8 (5) + 0 = ",
        value: 5,
        suffix: " Fire",
        className: "attack-damage-total",
    });
    assert.equal(formatAttackResult(result).length, 2);
});

test("bolds the attack count in a Multiattack description", () => {
    assert.deepEqual(
        splitAttackCount("The tarrasque makes five attacks: one with its bite."),
        [
            { text: "The tarrasque makes ", bold: false },
            { text: "five", bold: true },
            { text: " attacks: one with its bite.", bold: false },
        ],
    );
});

test("formats the final attack roll with its emphasis class", (t) => {
    t.mock.method(Math, "random", () => 0.5);
    const result = rollAttack({
        attack_bonus: 4,
        dc: null,
        dc_type: "",
        dc_success: "",
        damage_components: [],
    });

    assert.deepEqual(formatAttackResult(result)[0], {
        prefix: "Attack Roll: (",
        rolls: [11],
        selectedIndex: 0,
        middle: ") + 4 = ",
        value: 15,
        className: "attack-roll-total",
    });
});

test("uses the higher d20 for advantage and the lower for disadvantage", (t) => {
    const values = [0.1, 0.9, 0.9, 0.1];
    t.mock.method(Math, "random", () => values.shift());
    const attack = {
        attack_bonus: 5,
        dc: null,
        dc_type: "",
        dc_success: "",
        damage_components: [],
    };

    const advantage = rollAttack(attack, "advantage");
    const disadvantage = rollAttack(attack, "disadvantage");

    assert.deepEqual(advantage.attackRoll, {
        rolls: [3, 19],
        selectedIndex: 1,
        die: 19,
        bonus: 5,
        total: 24,
    });
    assert.deepEqual(formatAttackResult(advantage)[0], {
        prefix: "Attack Roll: (",
        rolls: [3, 19],
        selectedIndex: 1,
        middle: ") + 5 = ",
        value: 24,
        className: "attack-roll-total",
    });
    assert.deepEqual(disadvantage.attackRoll, {
        rolls: [19, 3],
        selectedIndex: 1,
        die: 3,
        bonus: 5,
        total: 8,
    });
});

test("formats negative damage modifiers and damage types", () => {
    const lines = formatAttackResult({
        attackRoll: null,
        dc: null,
        dcType: "",
        dcSuccess: "",
        damageComponents: [
            {
                dice: "1d4",
                rolls: [3],
                modifier: -1,
                damage_type: "Cold",
                total: 2,
            },
        ],
        damageTotal: 2,
    });

    assert.deepEqual(lines[1], {
        prefix: "Damage: 1d4 (3) - 1 = ",
        value: 2,
        suffix: " Cold",
        className: "attack-damage-total",
    });
});
