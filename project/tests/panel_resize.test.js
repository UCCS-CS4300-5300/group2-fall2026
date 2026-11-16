import test from "node:test";
import assert from "node:assert/strict";
import { clampToolsWidth } from "../core/static/core/js/panel_resize.js";

test("lets the tools panel grow and shrink within the available space", () => {
    assert.equal(clampToolsWidth(500, 1270), 500);
    assert.equal(clampToolsWidth(340, 1270), 340);
});

test("keeps the tools controls visible when dragged too far right", () => {
    assert.equal(clampToolsWidth(80, 1270), 300);
    assert.equal(clampToolsWidth(300, 1270), 300);
});

test("leaves room for the encounter when dragged too far left", () => {
    assert.equal(clampToolsWidth(1200, 1270), 910);
    assert.equal(clampToolsWidth(910, 1270), 910);
});

test("reclamps a wide panel when the window gets smaller", () => {
    assert.equal(clampToolsWidth(800, 890), 530);
    assert.equal(clampToolsWidth(530, 791), 431);
});
