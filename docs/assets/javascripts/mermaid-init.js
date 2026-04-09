window.mermaidConfig = {
  startOnLoad: false,
  securityLevel: "loose",
};

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
