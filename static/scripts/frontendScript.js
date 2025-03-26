let c = document.getElementById("warehouseCanvas");
let ctx = c.getContext("2d");

// Adjust for high DPI screens
let dpr = window.devicePixelRatio || 1; // Get device pixel ratio
let rect = c.getBoundingClientRect(); // Get canvas's display size

c.width = rect.width * dpr; // Set actual width
c.height = rect.height * dpr; // Set actual height

ctx.scale(dpr, dpr); // Scale the context

// Adjust coordinates for sharp lines

// Create a Grid for the Warehouse
let gridSize = Math.floor(c.height / 21);

/*
let numGridsHeight = Math.floor(c.height / gridSize);
let numGridsWidth = Math.floor(c.width / gridSize);
for (let i = 0; i < c.width; i += gridSize) {
    ctx.moveTo(i, 0);
    ctx.lineTo(i, c.height);
    ctx.stroke();
    ctx.moveTo(0, i);
    ctx.lineTo(c.width, i);
    ctx.stroke();

}*/
drawPackingTable(gridSize, c.height, c.width);
//drawStorageShelfRow(gridSize, c.height - gridSize * 7, gridSize, gridSize * 6, 5);
//drawStorageShelfRow(gridSize, c.height - gridSize * 14, gridSize, gridSize * 6, 5);
drawStorageShelfFloorPlan(7, 2, gridSize, c.height, c.width);

// Create the Packing Table (Rectangle)
function drawPackingTable(gridSize, screenHeight, screenWidth) {
    let rectX = (((screenWidth / gridSize) / 2) - 1) * gridSize;
    let rectWidth = gridSize * 2;
    ctx.rect(rectX, gridSize, rectWidth, gridSize); // x, y, width, height
    ctx.fillStyle = "lightblue";
    ctx.fill(); // Draw the outline

// Set text styles
    ctx.font = "15px Arial";
    ctx.fillStyle = "black";
    ctx.textAlign = "center"; // Horizontal alignment
    ctx.textBaseline = "middle"; // Vertical alignment

// Calculate text position (center of the rectangle)
    let textX = rectX + rectWidth / 2; // Corrected calculation
    let textY = gridSize + gridSize / 2;

    ctx.fillText("Packing Table", textX, textY);
}

function drawStorageShelf(positionX, positionY, gridSize, shelfHeight) {
    ctx.rect(positionX, positionY, 2 * gridSize, shelfHeight); // x, y, width, height
    ctx.fillStyle = "lightblue";
    ctx.fill(); // Draw the outline

}

function drawStorageShelfRow(startPositionX, startPositionY, gridSize, shelfHeight, numberOfShelfs) {
    let startPosition = 0;
    for (let i = 0; i < numberOfShelfs; i++) {
        drawStorageShelf(startPosition, startPositionY, gridSize, gridSize * 6);
        startPosition = startPosition + 5 * gridSize;
    }
}

function drawStorageShelfFloorPlan(numAisles, numCrossing, gridSize, screenHeight, screenWidth) {
    let marginTop = 3;
    let startPositionY = c.height - gridSize * 7;
    for (let i = 0; i < numCrossing; i++) {
        drawStorageShelfRow(gridSize, startPositionY, gridSize, gridSize * 6, numAisles);
        startPositionY -= gridSize * 7;
    }
}