function isDarkScheme() {
  return document.body.getAttribute("data-md-color-scheme") === "slate";
}

function getMermaidThemeVariables() {
  if (isDarkScheme()) {
    return {
      primaryColor: "#123342",
      primaryTextColor: "#e7eef5",
      primaryBorderColor: "#5ec4be",
      lineColor: "#9ec4d1",
      secondaryColor: "#0f2432",
      tertiaryColor: "#153040",
      background: "#0b1120",
      mainBkg: "#153040",
      secondBkg: "#112738",
      tertiaryBkg: "#0f2030",
      textColor: "#e7eef5",
      labelTextColor: "#e7eef5",
      edgeLabelBackground: "#0f2432",
      nodeBorder: "#5ec4be",
      clusterBkg: "#102536",
      clusterBorder: "#4ca9a8",
      titleColor: "#f4f8ff",
      actorTextColor: "#e7eef5",
      actorLineColor: "#9ec4d1",
      signalColor: "#9ec4d1",
      signalTextColor: "#e7eef5",
      noteTextColor: "#e7eef5",
      noteBkgColor: "#153040",
      noteBorderColor: "#5ec4be",
      activationBorderColor: "#6ccfc4",
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
  return {
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    themeVariables: getMermaidThemeVariables(),
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
