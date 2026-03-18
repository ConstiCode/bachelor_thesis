/**
 * BenchmarkCharts — Statistical analysis and Plotly.js rendering for benchmark results.
 *
 * Produces 6 scientific-quality plots suitable for a bachelor thesis:
 * 1. Route Length vs Product Count (line + error bars)
 * 2. Computation Time vs Product Count (line + error bars, log Y)
 * 3. Optimality Gap vs Product Count (line + error bars)
 * 4. Grouped Box Plot of Route Lengths
 * 5. Grouped Bar Chart by Warehouse Config
 * 6. Heatmap of Optimality Gap (Product Count x Warehouse Config)
 */

const ALGO_META = {
    nearestNeighbor:  { name: "Nearest Neighbor", color: "#d62728", symbol: "circle" },
    christofides:     { name: "Christofides",     color: "#ff7f0e", symbol: "square" },
    fixedParameter:   { name: "Fixed Parameter (DP)",  color: "#1f77b4", symbol: "diamond" },
    scfsPlus:         { name: "SCFS+ (MILP)",         color: "#2ca02c", symbol: "triangle-up" },
};

/** Scientific layout defaults — white bg, Arial, no title (caption goes in thesis). */
const BASE_LAYOUT = {
    font: { family: "Arial, Helvetica, sans-serif", size: 13, color: "#333" },
    paper_bgcolor: "#ffffff",
    plot_bgcolor:  "#ffffff",
    margin: { t: 30, r: 30, b: 60, l: 70 },
    legend: { orientation: "h", y: -0.2, x: 0.5, xanchor: "center" },
    hovermode: "x unified",
};

/** Plotly config — download buttons for SVG and PNG. */
const PLOT_CONFIG = {
    responsive: true,
    toImageButtonOptions: { format: "svg", filename: "plot", scale: 2 },
    modeBarButtonsToAdd: [
        {
            name: "Download PNG",
            icon: Plotly.Icons.camera,
            click: (gd) => Plotly.downloadImage(gd, { format: "png", width: 800, height: 500, filename: gd.id, scale: 3 })
        },
        {
            name: "Download SVG",
            icon: Plotly.Icons.disk,
            click: (gd) => Plotly.downloadImage(gd, { format: "svg", width: 800, height: 500, filename: gd.id })
        }
    ],
    displaylogo: false,
};


// =============================================================================
// Statistical helpers
// =============================================================================

function mean(arr) {
    return arr.reduce((s, v) => s + v, 0) / arr.length;
}

function stdDev(arr) {
    const m = mean(arr);
    return Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / (arr.length - 1));
}

function ci95(arr) {
    if (arr.length < 2) return 0;
    return 1.96 * (stdDev(arr) / Math.sqrt(arr.length));
}

/**
 * Groups results by a key function, returning a Map of key → [results].
 */
function groupBy(results, keyFn) {
    const map = new Map();
    for (const r of results) {
        const key = keyFn(r);
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(r);
    }
    return map;
}

/**
 * Computes the optimality gap (%) for each result row.
 * Reference = best (minimum) route_length among all algorithms for the same instance
 * (same config + product_count + iteration).
 */
function addOptimalityGap(results) {
    const okResults = results.filter(r => r.status === "ok");
    const instanceKey = r => `${r.num_columns}-${r.num_crossings}-${r.num_products}-${r.iteration}`;

    // Find best length per instance
    const bestPerInstance = new Map();
    for (const r of okResults) {
        const key = instanceKey(r);
        if (!bestPerInstance.has(key) || r.route_length < bestPerInstance.get(key)) {
            bestPerInstance.set(key, r.route_length);
        }
    }

    // Compute gap
    for (const r of okResults) {
        const best = bestPerInstance.get(instanceKey(r));
        r.optimality_gap = best > 0 ? ((r.route_length - best) / best) * 100 : 0;
    }

    return okResults;
}


// =============================================================================
// Plot 1: Route Length vs Product Count
// =============================================================================

function plotRouteLength(results) {
    const okResults = results.filter(r => r.status === "ok");
    const algorithms = [...new Set(okResults.map(r => r.algorithm))];
    const productCounts = [...new Set(okResults.map(r => r.num_products))].sort((a, b) => a - b);

    const traces = algorithms.map(algo => {
        const algoData = okResults.filter(r => r.algorithm === algo);
        const yMeans = [], yErrors = [];

        for (const pc of productCounts) {
            const values = algoData.filter(r => r.num_products === pc).map(r => r.route_length);
            yMeans.push(values.length ? mean(values) : null);
            yErrors.push(values.length >= 2 ? ci95(values) : 0);
        }

        const meta = ALGO_META[algo] || { name: algo, color: "#999", symbol: "circle" };
        return {
            x: productCounts,
            y: yMeans,
            error_y: { type: "data", array: yErrors, visible: true, thickness: 1.5 },
            mode: "lines+markers",
            name: meta.name,
            marker: { symbol: meta.symbol, size: 7 },
            line: { color: meta.color, width: 2 },
        };
    });

    const layout = {
        ...BASE_LAYOUT,
        xaxis: { title: "Number of Products", dtick: productCounts.length <= 10 ? undefined : "auto" },
        yaxis: { title: "Mean Route Length (units)" },
    };

    Plotly.newPlot("plotRouteLength", traces, layout, PLOT_CONFIG);
}


// =============================================================================
// Plot 2: Computation Time vs Product Count (log scale)
// =============================================================================

function plotComputationTime(results) {
    const okResults = results.filter(r => r.status === "ok");
    const algorithms = [...new Set(okResults.map(r => r.algorithm))];
    const productCounts = [...new Set(okResults.map(r => r.num_products))].sort((a, b) => a - b);

    const traces = algorithms.map(algo => {
        const algoData = okResults.filter(r => r.algorithm === algo);
        const yMeans = [], yErrors = [];

        for (const pc of productCounts) {
            const values = algoData.filter(r => r.num_products === pc).map(r => r.computation_time_ms);
            yMeans.push(values.length ? mean(values) : null);
            yErrors.push(values.length >= 2 ? ci95(values) : 0);
        }

        const meta = ALGO_META[algo] || { name: algo, color: "#999", symbol: "circle" };
        return {
            x: productCounts,
            y: yMeans,
            error_y: { type: "data", array: yErrors, visible: true, thickness: 1.5 },
            mode: "lines+markers",
            name: meta.name,
            marker: { symbol: meta.symbol, size: 7 },
            line: { color: meta.color, width: 2 },
        };
    });

    const layout = {
        ...BASE_LAYOUT,
        xaxis: { title: "Number of Products" },
        yaxis: { title: "Mean Computation Time (ms)", type: "log" },
    };

    Plotly.newPlot("plotComputationTime", traces, layout, PLOT_CONFIG);
}


// =============================================================================
// Plot 3: Optimality Gap vs Product Count
// =============================================================================

function plotOptimalityGap(results) {
    const okResults = addOptimalityGap(results);
    const algorithms = [...new Set(okResults.map(r => r.algorithm))];
    const productCounts = [...new Set(okResults.map(r => r.num_products))].sort((a, b) => a - b);

    const traces = algorithms.map(algo => {
        const algoData = okResults.filter(r => r.algorithm === algo);
        const yMeans = [], yErrors = [];

        for (const pc of productCounts) {
            const values = algoData.filter(r => r.num_products === pc).map(r => r.optimality_gap);
            yMeans.push(values.length ? mean(values) : null);
            yErrors.push(values.length >= 2 ? ci95(values) : 0);
        }

        const meta = ALGO_META[algo] || { name: algo, color: "#999", symbol: "circle" };
        return {
            x: productCounts,
            y: yMeans,
            error_y: { type: "data", array: yErrors, visible: true, thickness: 1.5 },
            mode: "lines+markers",
            name: meta.name,
            marker: { symbol: meta.symbol, size: 7 },
            line: { color: meta.color, width: 2 },
        };
    });

    const layout = {
        ...BASE_LAYOUT,
        xaxis: { title: "Number of Products" },
        yaxis: { title: "Mean Optimality Gap (%)" },
    };

    Plotly.newPlot("plotOptimalityGap", traces, layout, PLOT_CONFIG);
}


// =============================================================================
// Plot 4: Grouped Box Plot
// =============================================================================

function plotBoxPlot(results) {
    const okResults = results.filter(r => r.status === "ok");
    const algorithms = [...new Set(okResults.map(r => r.algorithm))];
    const productCounts = [...new Set(okResults.map(r => r.num_products))].sort((a, b) => a - b);

    const traces = [];

    for (const algo of algorithms) {
        const algoData = okResults.filter(r => r.algorithm === algo);
        const meta = ALGO_META[algo] || { name: algo, color: "#999" };

        traces.push({
            type: "box",
            name: meta.name,
            x: algoData.map(r => `${r.num_products} products`),
            y: algoData.map(r => r.route_length),
            marker: { color: meta.color },
            boxmean: "sd",
        });
    }

    const layout = {
        ...BASE_LAYOUT,
        boxmode: "group",
        xaxis: { title: "Product Count" },
        yaxis: { title: "Route Length (units)" },
    };

    Plotly.newPlot("plotBoxPlot", traces, layout, PLOT_CONFIG);
}


// =============================================================================
// Plot 5: Grouped Bar Chart by Warehouse Config
// =============================================================================

function plotByWarehouse(results) {
    const okResults = results.filter(r => r.status === "ok");
    const algorithms = [...new Set(okResults.map(r => r.algorithm))];
    const configs = [...new Set(okResults.map(r => `${r.num_columns}x${r.num_crossings}`))];

    const traces = algorithms.map(algo => {
        const algoData = okResults.filter(r => r.algorithm === algo);
        const meta = ALGO_META[algo] || { name: algo, color: "#999" };

        const yMeans = [], yErrors = [];
        for (const cfg of configs) {
            const [cols, rows] = cfg.split("x").map(Number);
            const values = algoData
                .filter(r => r.num_columns === cols && r.num_crossings === rows)
                .map(r => r.route_length);
            yMeans.push(values.length ? mean(values) : 0);
            yErrors.push(values.length >= 2 ? ci95(values) : 0);
        }

        return {
            type: "bar",
            name: meta.name,
            x: configs,
            y: yMeans,
            error_y: { type: "data", array: yErrors, visible: true, thickness: 1.5 },
            marker: { color: meta.color },
        };
    });

    const layout = {
        ...BASE_LAYOUT,
        barmode: "group",
        xaxis: { title: "Warehouse Configuration (Columns x Rows)" },
        yaxis: { title: "Mean Route Length (units)" },
    };

    Plotly.newPlot("plotByWarehouse", traces, layout, PLOT_CONFIG);
}


// =============================================================================
// Plot 6: Heatmap — Optimality Gap by Product Count x Warehouse Config
// =============================================================================

function plotHeatmap(results) {
    const okResults = addOptimalityGap(results);

    // Only show heuristics (NN, Christofides) since FP is the reference (gap ~0)
    const heuristics = okResults.filter(r => r.algorithm !== "fixedParameter" && r.algorithm !== "scfsPlus");
    if (heuristics.length === 0) {
        // If only exact algorithms were selected, show a message instead
        Plotly.newPlot("plotHeatmap", [], {
            ...BASE_LAYOUT,
            annotations: [{ text: "Heatmap requires at least one heuristic algorithm", showarrow: false, font: { size: 14 } }],
            xaxis: { visible: false }, yaxis: { visible: false },
        }, PLOT_CONFIG);
        return;
    }

    const productCounts = [...new Set(heuristics.map(r => r.num_products))].sort((a, b) => a - b);
    const configs = [...new Set(heuristics.map(r => `${r.num_columns}x${r.num_crossings}`))];

    // Build z-matrix: rows = configs, cols = product counts
    const z = configs.map(cfg => {
        const [cols, rows] = cfg.split("x").map(Number);
        return productCounts.map(pc => {
            const values = heuristics
                .filter(r => r.num_columns === cols && r.num_crossings === rows && r.num_products === pc)
                .map(r => r.optimality_gap);
            return values.length ? parseFloat(mean(values).toFixed(2)) : null;
        });
    });

    const trace = {
        type: "heatmap",
        z: z,
        x: productCounts.map(String),
        y: configs,
        colorscale: "YlOrRd",
        colorbar: { title: "Gap (%)", titleside: "right" },
        hoverongaps: false,
        text: z.map(row => row.map(v => v !== null ? `${v.toFixed(1)}%` : "")),
        texttemplate: "%{text}",
        textfont: { size: 12 },
    };

    const layout = {
        ...BASE_LAYOUT,
        xaxis: { title: "Number of Products", type: "category" },
        yaxis: { title: "Warehouse Config (Col x Row)", type: "category" },
    };

    Plotly.newPlot("plotHeatmap", [trace], layout, PLOT_CONFIG);
}


// =============================================================================
// Public API
// =============================================================================

export function renderAllCharts(results) {
    plotRouteLength(results);
    plotComputationTime(results);
    plotOptimalityGap(results);
    plotBoxPlot(results);
    plotByWarehouse(results);
    plotHeatmap(results);
}