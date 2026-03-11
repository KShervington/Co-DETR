import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF
import matplotlib.pyplot as plt

# Hardcoded JSON data from your query
HARDCODED_DATA = {
    "coordinates": [
        [28.60063362121582, -81.20477294921875], [28.60141944885254, -81.19973754882812],
        [28.60950660705566, -81.1920394897461], [28.60072326660156, -81.19657897949219],
        [28.60756301879883, -81.20382690429688], [28.5991153717041, -81.20597076416016],
        [28.60526275634766, -81.20201110839844], [28.59173965454102, -81.18913269042969],
        [28.5957202911377, -81.1987533569336], [28.60433769226074, -81.19009399414062]
    ],
    "values": [
        633.8900146484375, 585.5999755859375, 341.4500122070313, 466.9200134277344,
        591.2899780273438, 1048.81005859375, 382.760009765625, 804.6099853515625,
        498.9100036621094, 341.0299987792969
    ]
}

def run_interpolation_test():
    print("Extracting data...")
    coords_array = np.array(HARDCODED_DATA["coordinates"])
    values_array = np.array(HARDCODED_DATA["values"])
    
    x_min, x_max = np.min(coords_array[:, 0]), np.max(coords_array[:, 0])
    y_min, y_max = np.min(coords_array[:, 1]), np.max(coords_array[:, 1])
    
    x_range = x_max - x_min
    y_range = y_max - y_min
    
    # 1. Establish a sane floor and ceiling
    lower_bound = 0.002 
    upper_bound = max(max(x_range, y_range), 0.05)
    
    # 2. Calculate a SINGLE starting length scale (averaging the spatial ranges)
    l_scale_start = max((x_range + y_range) / 4, lower_bound)
    
    # 3. Pass a single value to length_scale to force circular (isotropic) interpolation
    kernel = RBF(
        length_scale=l_scale_start,
        length_scale_bounds=(lower_bound, upper_bound) 
    )
    
    print("Fitting Gaussian Process Regressor...")
    # 4. Small alpha to trust sensor readings
    reg = GaussianProcessRegressor(
        kernel=kernel, 
        alpha=1e-4, 
        normalize_y=True,
        n_restarts_optimizer=5,
        random_state=42
    )
    
    reg.fit(X=coords_array, y=values_array)
    
    print("Predicting grid...")
    grid_resolution = 50
    x_grid = np.linspace(x_min, x_max, grid_resolution)
    y_grid = np.linspace(y_min, y_max, grid_resolution)
    
    xx, yy = np.meshgrid(x_grid, y_grid)
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    
    predicted_values = reg.predict(grid_points)
    
    # --- Visualization (Added for local testing) ---
    print("Generating plot...")
    plt.figure(figsize=(10, 8))
    
    # Reshape predictions back to 2D grid for contour plotting
    zz = predicted_values.reshape(grid_resolution, grid_resolution)
    
    # Plot the interpolated surface
    contour = plt.contourf(xx, yy, zz, levels=20, cmap='viridis', alpha=0.8)
    plt.colorbar(contour, label='CO2 Levels')
    
    # Plot the original sensor locations
    scatter = plt.scatter(coords_array[:, 0], coords_array[:, 1], 
                          c=values_array, cmap='viridis', edgecolors='white', 
                          linewidth=1.5, s=100, label='Sensors')
    
    plt.title("CO2 Surface Interpolation Test")
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")
    plt.legend()
    plt.tight_layout()
    plt.show()

    return {
        "status": "success", 
        "grid_points_shape": grid_points.shape,
        "predictions_shape": predicted_values.shape
    }

if __name__ == "__main__":
    result = run_interpolation_test()
    print("Test completed successfully:", result)