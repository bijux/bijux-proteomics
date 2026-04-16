function isDarkScheme() {
  return document.body.getAttribute("data-md-color-scheme") === "slate";
}

function getMermaidThemeVariables() {
  if (isDarkScheme()) {
    return {
      primaryColor: "#163c4c",
      primaryTextColor: "#e7eef5",
      primaryBorderColor: "#7ddad4",
      lineColor: "#b7d8e2",
      secondaryColor: "#112c3c",
      tertiaryColor: "#19384a",
      background: "#0b1120",
      mainBkg: "#19384a",
      secondBkg: "#132f40",
      tertiaryBkg: "#102838",
      textColor: "#e7eef5",
      labelTextColor: "#e7eef5",
      edgeLabelBackground: "#1a3345",
      nodeBorder: "#7ddad4",
      clusterBkg: "#11293a",
      clusterBorder: "#5cc3bd",
      titleColor: "#f4f8ff",
      actorTextColor: "#e7eef5",
      actorLineColor: "#b7d8e2",
      signalColor: "#b7d8e2",
      signalTextColor: "#e7eef5",
      noteTextColor: "#e7eef5",
      noteBkgColor: "#1a3a4d",
      noteBorderColor: "#7ddad4",
      activationBorderColor: "#7ddad4",
      sequenceNumberColor: "#e7eef5",
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
    .label, .label text, .nodeLabel, .edgeLabel, .edgeLabel p {
      fill: #e7eef5 !important;
      color: #e7eef5 !important;
    }
    .edgeLabel rect {
      fill: #1a3345 !important;
      opacity: 1 !important;
    }
    .cluster rect {
      fill: #11293a !important;
      stroke: #5cc3bd !important;
    }
    .node rect, .node circle, .node ellipse, .node polygon, .node path {
      stroke: #7ddad4 !important;
    }
    .flowchart-link, .marker, .marker path, .path {
      stroke: #b7d8e2 !important;
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
