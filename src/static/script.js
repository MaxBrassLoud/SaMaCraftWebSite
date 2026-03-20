// ==========================
// 🌗 Dark/Light Theme
// ==========================
const themeToggle = document.getElementById("theme-toggle");
if (themeToggle) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const savedTheme = localStorage.getItem("theme") || (prefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggle.textContent = savedTheme === "dark" ? "☀️" : "🌙";

  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    themeToggle.textContent = next === "dark" ? "☀️" : "🌙";
  });
}

// ==========================
// 🍔 Hamburger Menu (Mobile)
// ==========================
function setupHamburger() {
  const hamburger = document.querySelector(".hamburger");
  const mobileNav = document.querySelector(".mobile-nav");
  if (!hamburger || !mobileNav) return;

  hamburger.addEventListener("click", () => {
    const isOpen = mobileNav.classList.toggle("open");
    hamburger.classList.toggle("open", isOpen);
  });

  mobileNav.querySelectorAll(".nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      mobileNav.classList.remove("open");
      hamburger.classList.remove("open");
    });
  });

  document.addEventListener("click", (e) => {
    if (!hamburger.contains(e.target) && !mobileNav.contains(e.target)) {
      mobileNav.classList.remove("open");
      hamburger.classList.remove("open");
    }
  });
}

// ==========================
// 📚 Sidebar Toggle (Rules Mobile)
// ==========================
function setupSidebarToggle() {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  let overlay = document.querySelector(".sidebar-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "sidebar-overlay";
    document.body.appendChild(overlay);
  }

  const hamburger = document.querySelector(".hamburger");
  const mobileNav = document.querySelector(".mobile-nav");
  if (!hamburger) return;

  if (!mobileNav) {
    hamburger.addEventListener("click", () => {
      const isOpen = sidebar.classList.toggle("open");
      hamburger.classList.toggle("open", isOpen);
      overlay.classList.toggle("active", isOpen);
    });

    overlay.addEventListener("click", () => {
      sidebar.classList.remove("open");
      hamburger.classList.remove("open");
      overlay.classList.remove("active");
    });

    sidebar.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        if (window.innerWidth <= 900) {
          sidebar.classList.remove("open");
          hamburger.classList.remove("open");
          overlay.classList.remove("active");
        }
      });
    });
  }
}

// ==========================
// 🔍 Regelwerk-Suchfunktion
// ==========================
const searchInput = document.getElementById("rule-search");
if (searchInput) {
  const sections = document.querySelectorAll("main.rules-content section");

  function removeHighlights(element) {
    const marks = element.querySelectorAll("mark");
    marks.forEach(mark => {
      const parent = mark.parentNode;
      parent.replaceChild(document.createTextNode(mark.textContent), mark);
      parent.normalize();
    });
  }

  function highlightText(element, query) {
    if (!query) return;
    const regex = new RegExp(`(${query})`, "gi");
    for (const node of element.childNodes) {
      if (node.nodeType === 3) {
        const matches = node.textContent.match(regex);
        if (matches) {
          const newNode = document.createElement("span");
          newNode.innerHTML = node.textContent.replace(regex, `<mark>$1</mark>`);
          node.replaceWith(newNode);
        }
      } else if (node.nodeType === 1 && node.tagName !== "MARK") {
        highlightText(node, query);
      }
    }
  }

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim();
    sections.forEach(section => {
      removeHighlights(section);
      if (!query) { section.style.display = ""; return; }
      const text = section.textContent.toLowerCase();
      if (text.includes(query.toLowerCase())) {
        section.style.display = "";
        highlightText(section, query);
      } else {
        section.style.display = "none";
      }
    });
  });
}

// ==========================
// 🧑‍💼 Team-Suchfunktion
// ==========================
const teamSearch = document.getElementById("search");
if (teamSearch) {
  const cards = document.querySelectorAll(".team-card");
  teamSearch.addEventListener("input", () => {
    const query = teamSearch.value.toLowerCase();
    cards.forEach(card => {
      const name = card.querySelector("h3").textContent.toLowerCase();
      const role = card.querySelector(".role").textContent.toLowerCase();
      card.style.display = (name.includes(query) || role.includes(query)) ? "" : "none";
    });
  });
}

// ==========================
// 🚀 Init
// ==========================
document.addEventListener("DOMContentLoaded", () => {
  setupHamburger();
  setupSidebarToggle();
});