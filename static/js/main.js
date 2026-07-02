/**
 * Fitness Buddy — Main JavaScript
 * Dark Mode + UI Interactions
 */

"use strict";

// ═══════════════════════════════════════════════════════════
//  DARK MODE
// ═══════════════════════════════════════════════════════════
const THEME_KEY = "fb_theme";

function getTheme() {
  return localStorage.getItem(THEME_KEY) ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  const icon = document.getElementById("darkIcon");
  if (icon) {
    icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
  }
  // Update Chart.js defaults if charts are on the page
  if (typeof Chart !== "undefined") {
    const textColor  = theme === "dark" ? "#8b949e" : "#57606a";
    const gridColor  = theme === "dark" ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.05)";
    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;
  }
}

function toggleTheme() {
  const current = getTheme();
  const next = current === "dark" ? "light" : "dark";
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply stored theme immediately
applyTheme(getTheme());

document.addEventListener("DOMContentLoaded", () => {
  // Apply again after DOM is ready to ensure icon updates
  applyTheme(getTheme());

  const btn = document.getElementById("darkModeToggle");
  if (btn) btn.addEventListener("click", toggleTheme);

  // ── Auto-dismiss flash messages after 5s ───────────────
  setTimeout(() => {
    document.querySelectorAll(".alert-dismissible").forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, 5000);

  // ── Animate elements on scroll ─────────────────────────
  initScrollAnimations();

  // ── Navbar scroll shrink ───────────────────────────────
  initNavbarShrink();

  // ── Active nav link ────────────────────────────────────
  highlightActiveNavLink();

  // ── Tooltips ───────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    bootstrap.Tooltip.getOrCreateInstance(el);
  });
});

// ═══════════════════════════════════════════════════════════
//  SCROLL ANIMATIONS
// ═══════════════════════════════════════════════════════════
function initScrollAnimations() {
  if (!("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-fade-in");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  document.querySelectorAll(
    ".feature-card, .testimonial-card, .stat-card, .meal-card"
  ).forEach(el => {
    el.style.opacity = "0";
    observer.observe(el);
  });
}

// ═══════════════════════════════════════════════════════════
//  NAVBAR
// ═══════════════════════════════════════════════════════════
function initNavbarShrink() {
  const navbar = document.getElementById("mainNavbar");
  if (!navbar) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 20) {
      navbar.classList.add("shadow-sm");
    } else {
      navbar.classList.remove("shadow-sm");
    }
  }, { passive: true });
}

function highlightActiveNavLink() {
  const path = window.location.pathname;
  document.querySelectorAll(".nav-link").forEach(link => {
    const href = link.getAttribute("href") || "";
    if (href === path || (path !== "/" && href !== "/" && path.startsWith(href.split("?")[0]))) {
      link.classList.add("active");
    }
  });
}

// ═══════════════════════════════════════════════════════════
//  HABIT TRACKER — range slider live labels
// ═══════════════════════════════════════════════════════════
function updateSlider(input, labelId, template) {
  const label = document.getElementById(labelId);
  if (label) label.textContent = template;
}

// ═══════════════════════════════════════════════════════════
//  FORM HELPERS
// ═══════════════════════════════════════════════════════════
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const icon = btn.querySelector("i");
  if (input.type === "password") {
    input.type = "text";
    icon && icon.classList.replace("bi-eye", "bi-eye-slash");
  } else {
    input.type = "password";
    icon && icon.classList.replace("bi-eye-slash", "bi-eye");
  }
}

// ═══════════════════════════════════════════════════════════
//  CHATBOT — auto-resize textarea
// ═══════════════════════════════════════════════════════════
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

// ═══════════════════════════════════════════════════════════
//  NOTIFICATIONS — mark as read on click
// ═══════════════════════════════════════════════════════════
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-mark-read]");
  if (!btn) return;
  const notifId = btn.dataset.markRead;
  try {
    await fetch(`/notifications/mark-read/${notifId}`, { method: "POST" });
    const card = document.getElementById(`notif-${notifId}`);
    if (card) card.classList.add("opacity-50");
  } catch (_) { /* silent */ }
});

// ═══════════════════════════════════════════════════════════
//  SMOOTH SCROLL for anchor links
// ═══════════════════════════════════════════════════════════
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener("click", (e) => {
    const target = document.querySelector(anchor.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// ═══════════════════════════════════════════════════════════
//  BMI LIVE CALCULATOR (used on profile page)
// ═══════════════════════════════════════════════════════════
function calcBMI() {
  const h = parseFloat(document.getElementById("heightInput")?.value || 0);
  const w = parseFloat(document.getElementById("weightInput")?.value || 0);
  const bmiEl  = document.getElementById("liveBMI");
  const catEl  = document.getElementById("liveBMICategory");
  if (!bmiEl || !catEl) return;

  if (h > 0 && w > 0) {
    const bmi = (w / ((h / 100) ** 2)).toFixed(1);
    bmiEl.textContent = bmi;
    let cat, col;
    if      (bmi < 18.5) { cat = "Underweight"; col = "#0dcaf0"; }
    else if (bmi < 25)   { cat = "Normal Weight"; col = "#198754"; }
    else if (bmi < 30)   { cat = "Overweight"; col = "#ffc107"; }
    else                 { cat = "Obese"; col = "#dc3545"; }
    catEl.textContent = bmi < 18.5 ? "Underweight" : bmi < 25 ? "Normal Weight" : bmi < 30 ? "Overweight" : "Obese";
    bmiEl.style.color = col;
  } else {
    bmiEl.textContent = "—";
    catEl.textContent = "Enter height & weight";
    bmiEl.style.color = "";
  }
}

// ═══════════════════════════════════════════════════════════
//  WEIGHT LOG MODAL (dashboard / progress)
// ═══════════════════════════════════════════════════════════
async function logWeight() {
  const input = document.getElementById("weightInput");
  if (!input) return;
  const val = parseFloat(input.value);
  if (!val || val < 20) {
    alert("Please enter a valid weight (20–300 kg).");
    return;
  }
  try {
    const res  = await fetch("/log-weight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weight_kg: val }),
    });
    const data = await res.json();
    if (data.status === "ok") {
      const modal = bootstrap.Modal.getInstance(document.getElementById("logWeightModal"));
      if (modal) modal.hide();
      location.reload();
    }
  } catch (err) {
    alert("Failed to log weight. Please try again.");
  }
}
