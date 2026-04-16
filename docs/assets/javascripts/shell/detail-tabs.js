(function () {
  const shell = (window.bijuxShell = window.bijuxShell || {});

  function syncDetailStripPresence() {
    const header = document.querySelector("[data-md-component='header']");
    if (!header) {
      return;
    }
    const hasVisibleDetailStrip = document.querySelector(
      "[data-bijux-nested-strip]"
    );
    header.setAttribute(
      "data-bijux-detail-visible",
      hasVisibleDetailStrip ? "true" : "false"
    );
  }

  function syncNestedStripActiveState() {
    const navState = shell.navState;
    if (!navState) {
      return;
    }

    const activeSitePath = navState.syncSiteTabActiveState();
    const currentPath = navState.normalizePath(window.location.pathname);
    let parentPath = activeSitePath;

    for (const strip of document.querySelectorAll("[data-bijux-nested-strip]")) {
      for (const item of strip.querySelectorAll(".bijux-tabs__item")) {
        item.classList.remove("bijux-tabs__item--active");
      }

      for (const link of strip.querySelectorAll("a[data-bijux-strip-path]")) {
        link.removeAttribute("aria-current");
      }

      const stripParentPath = navState.normalizePath(
        strip.getAttribute("data-bijux-strip-parent-path") || "/"
      );
      const stripMatchesParent = parentPath && stripParentPath === parentPath;
      strip.hidden = !stripMatchesParent;

      if (!stripMatchesParent) {
        continue;
      }

      const authoredActiveLink = strip.querySelector(
        "a[data-bijux-strip-path][aria-current='page'], .bijux-tabs__item--active a[data-bijux-strip-path]"
      );
      let activeLink = navState.bestMatchingLink(
        strip,
        "data-bijux-strip-path",
        currentPath,
        "a[data-bijux-strip-path]"
      );

      if (activeLink) {
        activeLink.node
          .closest(".bijux-tabs__item")
          ?.classList.add("bijux-tabs__item--active");
        activeLink.node.setAttribute("aria-current", "page");
        parentPath = activeLink.path;
        continue;
      }

      if (authoredActiveLink) {
        authoredActiveLink
          .closest(".bijux-tabs__item")
          ?.classList.add("bijux-tabs__item--active");
        authoredActiveLink.setAttribute("aria-current", "page");
        parentPath = navState.normalizePath(
          authoredActiveLink.getAttribute("data-bijux-strip-path") || "/"
        );
        continue;
      }
      const firstLink = strip.querySelector("a[data-bijux-strip-path]");
      if (firstLink) {
        firstLink.closest(".bijux-tabs__item")?.classList.add("bijux-tabs__item--active");
        firstLink.setAttribute("aria-current", "page");
        parentPath = navState.normalizePath(
          firstLink.getAttribute("data-bijux-strip-path") || "/"
        );
      }
    }
  }

  function bindDetailSelectNavigation() {
    for (const select of document.querySelectorAll("[data-bijux-detail-select]")) {
      if (select.dataset.bijuxDetailSelectBound === "true") {
        continue;
      }

      select.dataset.bijuxDetailSelectBound = "true";
      select.addEventListener("change", () => {
        if (!select.value) {
          return;
        }
        window.location.href = select.value;
      });
    }
  }

  function syncDetailSelectState() {
    const navState = shell.navState;
    if (!navState) {
      return;
    }

    const strips = document.querySelectorAll(
      "[data-bijux-nested-strip]:not([hidden])"
    );

    for (const strip of strips) {
      const activeLink = strip.querySelector(
        "a[data-bijux-strip-path][aria-current='page']"
      );

      if (!activeLink) {
        continue;
      }

      const activePath = navState.normalizePath(
        activeLink.getAttribute("data-bijux-strip-path") ||
          "/"
      );

      const select = strip.querySelector("[data-bijux-detail-select]");
      if (!select) {
        continue;
      }

      for (const option of select.options) {
        const optionPath = navState.normalizePath(
          option.getAttribute("data-bijux-strip-path") ||
            option.value ||
            "/"
        );
        option.selected = optionPath === activePath;
      }
    }
  }

  function runDetailTabsSync() {
    syncNestedStripActiveState();
    syncDetailStripPresence();
    syncDetailSelectState();
    bindDetailSelectNavigation();
  }

  shell.detailTabs = {
    syncDetailStripPresence,
    syncNestedStripActiveState,
    syncDetailSelectState,
    bindDetailSelectNavigation,
    runDetailTabsSync,
  };
})();
