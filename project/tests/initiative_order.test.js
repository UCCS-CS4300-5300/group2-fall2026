import test from "node:test";
import assert from "node:assert/strict";
import { orderCombatants } from "../core/static/core/js/initiative_roller.js";

function card(id, initiative) {
    return { dataset: { id: String(id), initValue: String(initiative) } };
}

function ids(cards) {
    return orderCombatants(cards).map((entry) => entry.dataset.id);
}

test("shows the highest initiative first", () => {
    assert.deepEqual(ids([card(1, 8), card(2, 20), card(3, 12)]), ["2", "3", "1"]);
});

test("breaks ties by entry ID even when cards arrive in another order", () => {
    assert.deepEqual(ids([card(12, 10), card(3, 10), card(2, 10)]), ["2", "3", "12"]);
});

test("keeps waiting combatants below everyone with initiative", () => {
    const cards = [card(4, 0), card(3, -2), card(2, 0), card(1, 5)];
    assert.deepEqual(ids(cards), ["1", "3", "2", "4"]);
});

test("does not reorder the original card collection", () => {
    const first = card(1, 8);
    const second = card(2, 16);
    const cards = [first, second];
    assert.deepEqual(orderCombatants(cards), [second, first]);
    assert.deepEqual(cards, [first, second]);
    assert.deepEqual(orderCombatants([]), []);
});
