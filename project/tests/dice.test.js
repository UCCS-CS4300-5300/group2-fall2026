import test from "node:test";
import assert from "node:assert/strict";
import { rollDice } from "../core/static/core/js/dice.js";

for (const sides of [4, 6, 8, 10, 12, 20]) {
    test(`d${sides} includes both ends of its range`, (t) => {
        const values = [0, 0.999999];
        const random = t.mock.method(Math, "random", () => values.shift());

        assert.deepEqual(rollDice(sides, 2), {
            sides,
            count: 2,
            rolls: [1, sides],
            total: 1 + sides,
        });
        assert.equal(random.mock.callCount(), 2);
    });
}

test("keeps each roll and adds them together", (t) => {
    const values = [0, 0.25, 0.5, 0.75, 0.999999];
    t.mock.method(Math, "random", () => values.shift());

    assert.deepEqual(rollDice(8, 5), {
        sides: 8,
        count: 5,
        rolls: [1, 3, 5, 7, 8],
        total: 24,
    });
});

for (const count of [1, 20]) {
    test(`can roll ${count} dice`, (t) => {
        const random = t.mock.method(Math, "random", () => 0.5);
        const result = rollDice(6, count);

        assert.equal(result.count, count);
        assert.deepEqual(result.rolls, Array(count).fill(4));
        assert.equal(result.total, 4 * count);
        assert.equal(random.mock.callCount(), count);
    });
}

test("rejects invalid dice before rolling", (t) => {
    const random = t.mock.method(Math, "random");
    for (const sides of [0, -6, 3, 100, 6.5, "6", "six", "", null, undefined, NaN, Infinity]) {
        assert.throws(() => rollDice(sides, 1), /Choose a d4/);
    }
    assert.equal(random.mock.callCount(), 0);
});

test("rejects invalid counts before rolling", (t) => {
    const random = t.mock.method(Math, "random");
    for (const count of [0, -1, 21, 1.5, "2", "two", "", null, undefined, NaN, Infinity]) {
        assert.throws(() => rollDice(6, count), /whole number of dice from 1 to 20/);
    }
    assert.equal(random.mock.callCount(), 0);
});

test("a new roll does not reuse the previous results", (t) => {
    const values = [0, 0.999999];
    t.mock.method(Math, "random", () => values.shift());

    const first = rollDice(20, 1);
    const second = rollDice(20, 1);

    assert.deepEqual(first.rolls, [1]);
    assert.deepEqual(second.rolls, [20]);
    assert.notEqual(first.rolls, second.rolls);
});
