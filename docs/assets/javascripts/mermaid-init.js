window.mermaidConfig = {
  startOnLoad: false,
  securityLevel: "loose",
};

document$.subscribe(() => {
  if (typeof mermaid === "undefined") {
    return;
  }

  mermaid.initialize(window.mermaidConfig);
  const nodes = document.querySelectorAll("pre.mermaid, div.mermaid");
  if (!nodes.length) {
    return;
  }

  mermaid.run({
    nodes,
  });
});
