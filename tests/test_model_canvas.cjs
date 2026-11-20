const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = readFileSync(path.join(__dirname, "../src/lib/model-canvas.js"), "utf8");

function makeCanvas(boxes) {
    const context = vm.createContext({});
    vm.runInContext(source, context);
    Object.assign(context, {
        canvas: { width: 800, height: 600 }, boxes,
        boxWidth: 200, boxHeight: 75, draw: () => {},
        scale: 1, offsetX: 0, offsetY: 0,
    });
    return context;
}

test("fitModelZoom keeps one class visible with a finite transform", () => {
    const context = makeCanvas([{ x: -400, y: -300 }]);
    context.fitModelZoom();
    const { scale, offsetX, offsetY } = context;
    assert.ok(Number.isFinite(scale) && scale > 0);
    assert.ok(Number.isFinite(offsetX) && Number.isFinite(offsetY));
    assert.ok(-400 * scale + offsetX > 0 && -400 * scale + offsetX < 800);
    assert.ok(-300 * scale + offsetY > 0 && -300 * scale + offsetY < 600);
});

test("fitModelZoom brings all boxes into the canvas, including their edges", () => {
    const boxes = [{ x: -200, y: -100 }, { x: 1800, y: 1200 }];
    const context = makeCanvas(boxes);
    context.fitModelZoom();
    for (const box of boxes) {
        assert.ok((box.x - 100) * context.scale + context.offsetX >= 0);
        assert.ok((box.x + 100) * context.scale + context.offsetX <= 800);
        assert.ok((box.y - 37.5) * context.scale + context.offsetY >= 0);
        assert.ok((box.y + 37.5) * context.scale + context.offsetY <= 600);
    }
});

test("fitModelZoom leaves an empty model alone", () => {
    const context = makeCanvas([]);
    context.fitModelZoom();
    assert.equal(context.scale, 1);
});

test("the z shortcut uses the safe zoom", () => {
    const context = makeCanvas([{ x: 0, y: 0 }]);
    context.fitZoom();
    assert.ok(Number.isFinite(context.scale));
});
