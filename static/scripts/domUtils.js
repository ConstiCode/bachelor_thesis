/**
 * Adds a location to the given table body.
 */
export function addLocationToTable(tableBody, location) {
    const row = document.createElement("tr");

    const cellNum = document.createElement("td");
    cellNum.textContent = location.location_number;

    const cellX = document.createElement("td");
    cellX.textContent = location.x;

    const cellY = document.createElement("td");
    cellY.textContent = location.y;

    row.append(cellNum, cellX, cellY);
    tableBody.appendChild(row);
}
