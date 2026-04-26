window.mermaidConfig = {
  startOnLoad: false,
  securityLevel: "loose",
  theme: "base",
  flowchart: {
    htmlLabels: true,
    useMaxWidth: false,
    curve: "basis",
  },
};

function activeMermaidTheme() {
  const scheme = document.body?.getAttribute("data-md-color-scheme") || "default";
  if (scheme === "slate") {
    return {
      themeVariables: {
        background: "#0b1120",
        primaryColor: "#0f2030",
        primaryTextColor: "#eaf2fa",
        primaryBorderColor: "#7dd3fc",
        secondaryColor: "#11273a",
        secondaryTextColor: "#eaf2fa",
        secondaryBorderColor: "#2dd4bf",
        tertiaryColor: "#132a3d",
        tertiaryTextColor: "#eaf2fa",
        tertiaryBorderColor: "#fbbf24",
        lineColor: "#9fb8c7",
        textColor: "#eaf2fa",
        mainBkg: "#0f2030",
        nodeBkg: "#0f2030",
        clusterBkg: "#102334",
        clusterBorder: "#4ba8a2",
        edgeLabelBackground: "#102334",
        fontFamily: "IBM Plex Sans, ui-sans-serif, system-ui, sans-serif",
      },
    };
  }
  return {
    themeVariables: {
      background: "#f4f6f4",
      primaryColor: "#eef6ff",
      primaryTextColor: "#153145",
      primaryBorderColor: "#2563eb",
      secondaryColor: "#eefbf3",
      secondaryTextColor: "#173622",
      secondaryBorderColor: "#16a34a",
      tertiaryColor: "#fff4da",
      tertiaryTextColor: "#6b3410",
      tertiaryBorderColor: "#d97706",
      lineColor: "#446273",
      textColor: "#153145",
      mainBkg: "#eef6ff",
      nodeBkg: "#eef6ff",
      clusterBkg: "#f8fbff",
      clusterBorder: "#7aa0b8",
      edgeLabelBackground: "#ffffff",
      fontFamily: "IBM Plex Sans, ui-sans-serif, system-ui, sans-serif",
    },
  };
}

function normalizeMermaidBlocks() {
  // Normalize superfences output (<pre class="mermaid"><code>...</code></pre>)
  // into <div class="mermaid">...</div> so Mermaid receives raw diagram text.
  const preNodes = document.querySelectorAll("pre.mermaid");
  preNodes.forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code) {
      return;
    }

    const div = document.createElement("div");
    div.className = "mermaid";
    div.textContent = code.textContent || "";
    pre.replaceWith(div);
  });
}

function prepareMermaidNodesForRerender() {
  const nodes = document.querySelectorAll("div.mermaid");
  nodes.forEach((node) => {
    const source = node.dataset.bijuxMermaidSource;
    if (!source) {
      return;
    }
    node.removeAttribute("data-processed");
    node.textContent = source;
  });
}

function renderMermaidDiagrams() {
  if (typeof mermaid === "undefined") {
    return;
  }

  mermaid.initialize({
    ...window.mermaidConfig,
    ...activeMermaidTheme(),
  });

  normalizeMermaidBlocks();
  const nodes = document.querySelectorAll("div.mermaid");
  if (!nodes.length) {
    return;
  }

  // Persist original Mermaid definitions once, before Mermaid mutates the node.
  // Never infer source back from rendered SVG text.
  for (const node of nodes) {
    if (node.dataset.bijuxMermaidSource) {
      continue;
    }
    if (node.querySelector("svg")) {
      continue;
    }
    node.dataset.bijuxMermaidSource = node.textContent || "";
  }

  mermaid.run({ nodes });
}

function captureScrollPosition() {
  return {
    x: window.scrollX || window.pageXOffset || 0,
    y: window.scrollY || window.pageYOffset || 0,
  };
}

function restoreScrollPosition(position) {
  if (!position) {
    return;
  }
  window.scrollTo(position.x, position.y);
}

document$.subscribe(() => {
  renderMermaidDiagrams();

  if (window.__bijuxMermaidThemeBound === true) {
    return;
  }

  window.__bijuxMermaidThemeBound = true;
  window.addEventListener("bijux:theme-change", (event) => {
    const targetScroll = event?.detail?.scroll || captureScrollPosition();
    prepareMermaidNodesForRerender();
    renderMermaidDiagrams();
    restoreScrollPosition(targetScroll);
    requestAnimationFrame(() => restoreScrollPosition(targetScroll));
    setTimeout(() => restoreScrollPosition(targetScroll), 80);
  });
});
