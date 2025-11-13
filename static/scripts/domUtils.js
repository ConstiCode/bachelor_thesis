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

/**
 * Updates the route information table with new data.
 */
export function updateRouteInfoTable(element, data) {
    // clear previous table
    element.innerHTML = "";
    // todo: check why the table is cleared to early
    const table = document.createElement("table");
    table.style.borderCollapse = "collapse"; // Use CSS classes instead, but this works

    // create the table header
    const thead = document.createElement("thead");
    const hr = document.createElement("tr");
    const headers = ["Algorithm", "Length (tiles)", "Walking Time (min)", "Cost ($)", "Computation (ms)"];
    headers.forEach(text => {
        const th = document.createElement("th");
        th.textContent = text;
        th.style.border = "1px solid #ccc";
        hr.appendChild(th);
    });
    thead.appendChild(hr);
    table.appendChild(thead);

    // get the body
    const tbody = document.createElement("tbody");

    if (data.nearestNeighbor) {
        const r = data.nearestNeighbor; // Simplified
        const row = document.createElement("tr");

        const cellName = document.createElement("td");
        cellName.textContent = "Nearest Neighbor";

        const cellLength = document.createElement("td");
        cellLength.textContent = r.length; // Your logic here

        row.append(cellName, cellLength /*, ...otherCells */);
        tbody.appendChild(row);
    }

    table.appendChild(tbody);
    element.appendChild(table);
}