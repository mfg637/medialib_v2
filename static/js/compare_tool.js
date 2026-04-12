class GradientGenerator {
  constructor(points, maxRange = 1020) {
    this.points = points.sort((a, b) => a[0] - b[0]);
    this.maxRange = maxRange;
    this.lut = this._generateLUT();
  }

  _generateLUT() {
    const lut = new Uint8ClampedArray((this.maxRange + 1) * 4);

    for (let i = 0; i < this.points.length - 1; i++) {
      const [startVal, startCol] = this.points[i];
      const [endVal, endCol] = this.points[i + 1];

      for (let j = startVal; j <= endVal; j++) {
        if (j > this.maxRange) break;

        const ratio = (j - startVal) / (endVal - startVal || 1);
        const idx = j * 4;

        lut[idx] = startCol[0] + (endCol[0] - startCol[0]) * ratio; // R
        lut[idx + 1] = startCol[1] + (endCol[1] - startCol[1]) * ratio; // G
        lut[idx + 2] = startCol[2] + (endCol[2] - startCol[2]) * ratio; // B
        lut[idx + 3] = startCol[3] + (endCol[3] - startCol[3]) * ratio; // A
      }
    }

    const lastPoint = this.points[this.points.length - 1];
    const lastVal = lastPoint[0];
    const lastCol = lastPoint[1];
    if (lastVal < this.maxRange) {
      for (let j = lastVal + 1; j <= this.maxRange; j++) {
        const idx = j * 4;
        lut[idx] = lastCol[0];
        lut[idx + 1] = lastCol[1];
        lut[idx + 2] = lastCol[2];
        lut[idx + 3] = lastCol[3];
      }
    }

    return lut;
  }

  getColor(value) {
    const val = Math.min(Math.max(0, value), this.maxRange);
    const idx = val * 4;
    return [
      this.lut[idx],
      this.lut[idx + 1],
      this.lut[idx + 2],
      this.lut[idx + 3],
    ];
  }
}

const availableGradients = {
  heat_gradient: new GradientGenerator(
    [
      [0, [0, 0, 0, 255]],
      [16, [0, 0, 255, 255]],
      [32, [0, 255, 255, 255]],
      [64, [0, 255, 0, 255]],
      [128, [255, 255, 0, 255]],
      [255, [255, 0, 0, 255]],
      [765, [255, 255, 255, 255]],
    ],
    1020,
  ),
  heat_gradient_transparent: new GradientGenerator(
    [
      [0, [0, 0, 0, 0]],
      [16, [0, 0, 255, 255]],
      [32, [0, 255, 255, 255]],
      [64, [0, 255, 0, 255]],
      [128, [255, 255, 0, 255]],
      [255, [255, 0, 0, 255]],
      [765, [255, 255, 255, 255]],
    ],
    1020,
  ),
  show_any_diff: new GradientGenerator(
    [
      [0, [0, 0, 0, 0]],
      [1, [255, 0, 0, 255]],
    ],
    1020,
  ),
};

gradientsList = [
  availableGradients.heat_gradient,
  availableGradients.heat_gradient_transparent,
  availableGradients.show_any_diff,
];

let current_gradient = availableGradients.heat_gradient_transparent;

window.changeGlobalGradient = function (gradientIndexStr) {
  const current_gradient_index = Number(gradientIndexStr);
  if (current_gradient_index < gradientsList.length) {
    current_gradient = gradientsList[current_gradient_index];
    const selectors = document.querySelectorAll(".gradient-select");
    selectors.forEach((select) => {
      select.selectedIndex = current_gradient_index;
    });

    CompareTool.reRenderAllActive();
  }
};

const CompareTool = {
  cache: new Map(),

  updateOverlay(slider, containerId) {
    const container = document.getElementById(`layers-${containerId}`);
    const overlay = container.querySelector(".overlay-layer");
    overlay.style.opacity = slider.value / 100;
  },

  async toggleHeatmap(reprId1, reprId2, containerId) {
    const container = document.getElementById(`layers-${containerId}`);
    const canvas = container.querySelector(".heatmap-layer");

    if (canvas.style.display === "block") {
      canvas.style.display = "none";
      return;
    }

    if (this.cache.has(containerId)) {
      canvas.style.display = "block";
      return;
    }

    try {
      const url = `/medialib/dynamic/image-processing/diff?repr_id1=${reprId1}&repr_id2=${reprId2}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("Network response was not ok");

      const width = parseInt(response.headers.get("X-Width"));
      const height = parseInt(response.headers.get("X-Height"));
      const buffer = await response.arrayBuffer();

      const data = new Uint16Array(buffer);

      this.renderHeatmap(canvas, data, width, height);
      canvas.style.display = "block";
      this.cache.set(containerId, {
        data: data,
        width: width,
        height: height,
        canvas: canvas,
      });
    } catch (err) {
      console.error("Heatmap error:", err);
      alert("Error loading diffmap");
    }
  },

  renderHeatmap(canvas, data, width, height) {
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    const imageData = ctx.createImageData(width, height);
    const pixels = imageData.data;

    const lut = current_gradient.lut;

    for (let i = 0; i < data.length; i++) {
      const value = data[i] > 1020 ? 1020 : data[i];
      const pixel_index = i * 4;
      const lut_index = value * 4;

      pixels[pixel_index] = lut[lut_index];
      pixels[pixel_index + 1] = lut[lut_index + 1];
      pixels[pixel_index + 2] = lut[lut_index + 2];
      pixels[pixel_index + 3] = lut[lut_index + 3];
    }
    ctx.putImageData(imageData, 0, 0);
  },
  reRenderAllActive() {
    this.cache.forEach((cacheItem, containerId) => {
      //if (cacheItem.canvas.style.display === 'block') {
      this.renderHeatmap(
        cacheItem.canvas,
        cacheItem.data,
        cacheItem.width,
        cacheItem.height,
      );
      //}
    });
  },
  toggleFullSize(containerId) {
    const container = document.getElementById(`layers-${containerId}`);
    if (container) {
      container.classList.toggle("width-fit");
    }
  },
};

window.updateOverlay = CompareTool.updateOverlay.bind(CompareTool);
window.toggleHeatmap = (r1, r2, cId) => CompareTool.toggleHeatmap(r1, r2, cId);
