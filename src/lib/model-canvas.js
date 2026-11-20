// Fit the SHACL maker canvas to the loaded model, including the full box edges.
function fitModelZoom() {
    if (!canvas || boxes.length === 0 || !canvas.width || !canvas.height) return;

    const minX = Math.min(...boxes.map((box) => box.x - boxWidth / 2));
    const maxX = Math.max(...boxes.map((box) => box.x + boxWidth / 2));
    const minY = Math.min(...boxes.map((box) => box.y - boxHeight / 2));
    const maxY = Math.max(...boxes.map((box) => box.y + boxHeight / 2));
    const contentWidth = maxX - minX;
    const contentHeight = maxY - minY;

    scale = Math.min(canvas.width / contentWidth, canvas.height / contentHeight, 1) * 0.8;
    offsetX = (canvas.width - contentWidth * scale) / 2 - minX * scale;
    offsetY = (canvas.height - contentHeight * scale) / 2 - minY * scale;
    draw();
}

// Use the same safe framing for the canvas's "z" shortcut.
fitZoom = fitModelZoom;
