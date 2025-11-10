export default class ApiService {

    async generateLocations(model, productCount) {
        try {
            const response = await fetch('/generate-test-locations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    warehouse_config: model.getConfigForAPI(), // The correct, minimal data
                    product_count: productCount
                })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error generating locations:', error);
            alert("Error generating locations. Check console.");
            return [];
        }
    }

    async calculateRoutes(model, locations, algorithms) {
        try {
            const response = await fetch('/calculate-route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    warehouse_config: model.getConfigForAPI(), // Correct data
                    locations: locations,
                    algorithms: algorithms
                    // The backend should know the packing_table from the config
                })
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Error calculating routes:', error);
            alert("Error calculating routes. Check console.");
            return {};
        }
    }
}