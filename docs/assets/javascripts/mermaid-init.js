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
});
