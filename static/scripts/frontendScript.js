let c = document.getElementById("warehouseCanvas");
let ctx = c.getContext("2d");

// Adjust for high DPI screens
let dpr = window.devicePixelRatio || 1; // Get device pixel ratio
let rect = c.getBoundingClientRect(); // Get canvas's display size

c.width = rect.width * dpr; // Set actual width
c.height = rect.height * dpr; // Set actual height

ctx.scale(dpr, dpr); // Scale the context

// Set the canvas background color
ctx.fillStyle = "#1e1e1e";
ctx.fillRect(0, 0, c.width, c.height);

// Adjust coordinates for sharp lines

// Create a Grid for the Warehouse
//let gridSize = Math.floor(c.height / 21);

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
//drawPackingTable(gridSize, c.height, c.width);
//drawStorageShelfRow(gridSize, c.height - gridSize * 7, gridSize, gridSize * 6, 5);
//drawStorageShelfRow(gridSize, c.height - gridSize * 14, gridSize, gridSize * 6, 5);


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

function drawStorageShelf(positionX, positionY, horizontalGridSize, shelfHeight) {
    ctx.beginPath();
    ctx.rect(positionX, positionY, 2 * horizontalGridSize, shelfHeight); // x, y, width, height
    ctx.fillStyle = "lightblue";
    ctx.fill(); // Draw the outline

}

function drawStorageShelfRow(startPositionY, horizontalGridSize, shelfHeight, numAisles, screenWidth) {
    let offset = (numAisles * 4 * horizontalGridSize) / 2;
    let startPosition = (screenWidth / 2) - offset;

    for (let i = 0; i < numAisles; i++) {
        drawStorageShelf(startPosition, startPositionY, horizontalGridSize, shelfHeight);
        startPosition = startPosition + 5 * horizontalGridSize;
    }
}

function drawStorageShelfFloorPlan(numAisles, numCrossing, screenHeight, screenWidth) {
    let marginTop = 3;
    let marginBottom = 2;

    // the grid sizes are dynamically calculated based on the number of aisles and the screen height
    let verticalGridSizeAmount = Math.floor(screenHeight / ((numCrossing * 7) + marginBottom + marginTop));
    let horizontalGridSizeAmount = Math.floor(screenWidth / (numAisles * 4));

    //let shelfHeight = Math.floor(screenHeight / ((numCrossing * 7) + marginTop + marginBottom));
    //let aisleSpacing = Math.floor(screenWidth / (numAisles * 6)); // Ensure spacing shrinks as aisles increase
    //let shelfWidth = aisleSpacing * 2;

    let verticalGridSize = Math.floor(screenHeight / verticalGridSizeAmount);
    let horizontalGridSize = Math.floor(screenWidth / horizontalGridSizeAmount);

    let offset = (numCrossing * 7 * verticalGridSize) / 2;
    let startPositionY = (screenHeight / 2) + offset;

    for (let i = 0; i < numCrossing; i++) {
        drawStorageShelfRow(startPositionY, horizontalGridSize, verticalGridSize * 6, numAisles, screenWidth);
        startPositionY -= verticalGridSize * 7;
    }
}

drawStorageShelfFloorPlan(4, 3, c.height, c.width);


