function isDarkScheme() {
  return document.body.getAttribute("data-md-color-scheme") === "slate";
}

function getMermaidThemeVariables() {
  if (isDarkScheme()) {
    return {
      darkMode: true,
      primaryColor: "#112838",
      primaryTextColor: "#eaf2fa",
      primaryBorderColor: "#6fc7c2",
      lineColor: "#a9c8d4",
      secondaryColor: "#0f2332",
      tertiaryColor: "#132c3d",
      background: "#0b1120",
      mainBkg: "#122b3c",
      secondBkg: "#0f2434",
      tertiaryBkg: "#0d2030",
      textColor: "#eaf2fa",
      labelTextColor: "#eaf2fa",
      edgeLabelBackground: "#102334",
      nodeBorder: "#6fc7c2",
      clusterBkg: "#0f2536",
      clusterBorder: "#4ba8a2",
      titleColor: "#f4f8ff",
      actorTextColor: "#eaf2fa",
      actorLineColor: "#a9c8d4",
      signalColor: "#a9c8d4",
      signalTextColor: "#eaf2fa",
      noteTextColor: "#eaf2fa",
      noteBkgColor: "#132b3c",
      noteBorderColor: "#6fc7c2",
      activationBorderColor: "#6fc7c2",
      sequenceNumberColor: "#eaf2fa",
    };
  }

  return {
    primaryColor: "#d9f2ef",
    primaryTextColor: "#142033",
    primaryBorderColor: "#0f766e",
    lineColor: "#356275",
    secondaryColor: "#ebf7f6",
    tertiaryColor: "#f3fbfb",
    background: "#ffffff",
    mainBkg: "#e7f5f2",
    secondBkg: "#eef8f7",
    tertiaryBkg: "#f5fbfa",
    textColor: "#142033",
    labelTextColor: "#142033",
    edgeLabelBackground: "#eef8f7",
    nodeBorder: "#0f766e",
    clusterBkg: "#f3fbfa",
    clusterBorder: "#5b9ba8",
    titleColor: "#10213b",
    actorTextColor: "#142033",
    actorLineColor: "#356275",
    signalColor: "#356275",
    signalTextColor: "#142033",
    noteTextColor: "#142033",
    noteBkgColor: "#eef8f7",
    noteBorderColor: "#5b9ba8",
    activationBorderColor: "#0f766e",
    sequenceNumberColor: "#142033",
  };
}

function buildMermaidConfig() {
  const darkThemeCss = `
    .label, .label text, .nodeLabel, .edgeLabel, .edgeLabel p,
    span.nodeLabel, .cluster-label text {
      fill: #eaf2fa !important;
      color: #eaf2fa !important;
    }
    foreignObject div, foreignObject span, .labelBkg {
      color: #eaf2fa !important;
      fill: #eaf2fa !important;
      background: transparent !important;
    }
    .edgeLabel rect {
      fill: #102334 !important;
      opacity: 1 !important;
    }
    .cluster rect {
      fill: #0f2536 !important;
      stroke: #4ba8a2 !important;
    }
    .node rect, .node circle, .node ellipse, .node polygon, .node path,
    .classBox, .stateGroup rect, .stateGroup path,
    rect.basic, rect.label-container {
      fill: #122b3c !important;
      stroke: #6fc7c2 !important;
    }
    .flowchart-link, .marker, .marker path, .path, .edgePath .path {
      stroke: #a9c8d4 !important;
    }
    .relationshipLabelBox {
      fill: #102334 !important;
      opacity: 1 !important;
    }
    .legend text, .classTitle, .state-title {
      fill: #eaf2fa !important;
    }
  `;

  return {
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    themeVariables: getMermaidThemeVariables(),
    themeCSS: isDarkScheme() ? darkThemeCss : "",
  };
}

function parseColor(value) {
  if (!value) {
    return null;
  }

  const color = value.trim().toLowerCase();

  if (color === "none" || color === "transparent") {
    return null;
  }

  const hex = color.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    let raw = hex[1];
    if (raw.length === 3) {
      raw = raw
        .split("")
        .map((ch) => ch + ch)
        .join("");
    }
    return {
      r: parseInt(raw.slice(0, 2), 16),
      g: parseInt(raw.slice(2, 4), 16),
      b: parseInt(raw.slice(4, 6), 16),
    };
  }

  const rgb = color.match(
    /^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*[0-9.]+\s*)?\)$/,
  );
  if (rgb) {
    return {
      r: Number(rgb[1]),
      g: Number(rgb[2]),
      b: Number(rgb[3]),
    };
  }

  return null;
}

function relativeLuminance(rgb) {
  if (!rgb) {
    return 0;
  }

  const channels = [rgb.r, rgb.g, rgb.b].map((v) => {
    const c = Math.max(0, Math.min(255, v)) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });

  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function firstColorValue(element, cssName) {
  const inlineStyle = element.style && element.style[cssName];
  if (inlineStyle) {
    return inlineStyle;
  }

  const attr = element.getAttribute(cssName);
  if (attr) {
    return attr;
  }

  const computed = window.getComputedStyle(element)[cssName];
  if (computed) {
    return computed;
  }

  return "";
}

function applyDarkContrastNormalization(root) {
  if (!isDarkScheme()) {
    return;
  }

  const palettes = {
    nodeFill: "#122b3c",
    nodeStroke: "#5dbbb5",
    clusterFill: "#0f2536",
    clusterStroke: "#4a9f9a",
    lineStroke: "#9ab9c6",
    edgeLabelBg: "#0f2334",
    text: "#e6eef7",
  };

  for (const svg of root.querySelectorAll(".mermaid svg")) {
    const nodeShapes = svg.querySelectorAll(
      ".node rect, .node circle, .node ellipse, .node polygon, .node path, " +
        ".classBox, .stateGroup rect, .stateGroup path, rect.basic, rect.label-container",
    );
    for (const el of nodeShapes) {
      const fill = firstColorValue(el, "fill");
      if (relativeLuminance(parseColor(fill)) > 0.35 || !fill) {
        el.style.fill = palettes.nodeFill;
      }
      el.style.stroke = palettes.nodeStroke;
    }

    const clusterShapes = svg.querySelectorAll(".cluster rect, .cluster polygon");
    for (const el of clusterShapes) {
      el.style.fill = palettes.clusterFill;
      el.style.stroke = palettes.clusterStroke;
    }

    const lines = svg.querySelectorAll(
      ".flowchart-link, .edgePath .path, .path, .marker path, line, polyline, path",
    );
    for (const el of lines) {
      const cls = (el.getAttribute("class") || "").toLowerCase();
      const isNodeGeometry =
        cls.includes("node") || cls.includes("classbox") || cls.includes("label-container");
      if (!isNodeGeometry) {
        el.style.stroke = palettes.lineStroke;
      }
    }

    const edgeLabelBg = svg.querySelectorAll(".edgeLabel rect, .labelBkg, .relationshipLabelBox");
    for (const el of edgeLabelBg) {
      el.style.fill = palettes.edgeLabelBg;
      el.style.opacity = "1";
    }

    const labels = svg.querySelectorAll(
      "text, tspan, .label, .label text, .nodeLabel, span.nodeLabel, " +
        ".edgeLabel, .edgeLabel p, .cluster-label text, .classTitle, .state-title, " +
        "foreignObject div, foreignObject span",
    );
    for (const el of labels) {
      el.style.color = palettes.text;
      el.style.fill = palettes.text;
    }
  }
}

function normalizeMermaidBlocks(root) {
  const blocks = root.querySelectorAll("pre.mermaid");

  for (const block of blocks) {
    const source = block.querySelector("code");
    const diagram = document.createElement("div");

    diagram.className = "mermaid";
    diagram.textContent = (source || block).textContent || "";

    block.replaceWith(diagram);
  }
}

document$.subscribe(() => {
  if (typeof mermaid === "undefined") {
    return;
  }

  window.mermaidConfig = buildMermaidConfig();
  mermaid.initialize(window.mermaidConfig);
  normalizeMermaidBlocks(document);

  const nodes = Array.from(document.querySelectorAll("div.mermaid")).filter(
    (node) => node.getAttribute("data-processed") !== "true",
  );
  if (!nodes.length) {
    return;
  }

  mermaid.run({
    nodes,
  });

  applyDarkContrastNormalization(document);
});
