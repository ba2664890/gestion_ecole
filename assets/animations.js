/* ═══════════════════════════════════════════════════════════════════════════
   SGA – animations.js
   Chargé automatiquement par Dash depuis /assets/
   GSAP-style animations + interactions enrichies
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  /* ─── Utilitaires ─── */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  /* ══════════════════════════════════════════════════════════
     1. INTERSECTION OBSERVER – Animate on scroll
  ══════════════════════════════════════════════════════════ */
  function initScrollAnimations() {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.animationPlayState = "running";
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );

    // Pause then observe all animated elements
    $$(".animate-fade-up, .animate-fade-up-1, .animate-fade-up-2, .animate-fade-up-3, .animate-fade-up-4").forEach(
      (el) => {
        el.style.animationPlayState = "paused";
        observer.observe(el);
      }
    );
  }

  /* ══════════════════════════════════════════════════════════
     2. KPI COUNTER ANIMATION
  ══════════════════════════════════════════════════════════ */
  function animateCounters() {
    $$(".kpi-value").forEach((el) => {
      const raw = el.textContent.trim();
      const numMatch = raw.match(/[\d,.]+/);
      if (!numMatch) return;

      const target = parseFloat(numMatch[0].replace(/,/g, ""));
      const suffix = raw.replace(numMatch[0], "");
      const prefix = raw.split(numMatch[0])[0];
      const duration = 1200;
      const start = performance.now();

      function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

      function tick(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const value = target * easeOutCubic(progress);
        const formatted = Number.isInteger(target)
          ? Math.round(value).toLocaleString("fr-FR")
          : value.toFixed(1);
        el.textContent = prefix + formatted + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }

      // Only animate if visible
      const io = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          requestAnimationFrame(tick);
          io.disconnect();
        }
      });
      io.observe(el);
    });
  }

  /* ══════════════════════════════════════════════════════════
     3. PROGRESS BAR ANIMATION
  ══════════════════════════════════════════════════════════ */
  function animateProgressBars() {
    $$(".progress-fill").forEach((bar) => {
      const targetWidth = bar.style.width || "0%";
      bar.style.width = "0%";

      const io = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
          setTimeout(() => {
            bar.style.transition = "width 0.9s cubic-bezier(0.4, 0, 0.2, 1)";
            bar.style.width = targetWidth;
          }, 100);
          io.disconnect();
        }
      });
      io.observe(bar);
    });
  }

  /* ══════════════════════════════════════════════════════════
     4. SIDEBAR ACTIVE STATE (URL-based)
  ══════════════════════════════════════════════════════════ */
  function updateSidebarActive() {
    const path = window.location.pathname;
    $$(".nav-item").forEach((item) => {
      const href = item.getAttribute("href");
      if (href && (href === path || (href !== "/" && path.startsWith(href)))) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });
  }

  /* ══════════════════════════════════════════════════════════
     5. MOBILE SIDEBAR TOGGLE
  ══════════════════════════════════════════════════════════ */
  function initMobileSidebar() {
    const sidebar = $("#sidebar");
    const toggleBtn = $("#mobile-menu-btn");
    if (!sidebar || !toggleBtn) return;

    // Show toggle on mobile
    if (window.innerWidth <= 768) {
      toggleBtn.style.display = "flex";
    }

    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });

    // Close sidebar when clicking outside
    document.addEventListener("click", (e) => {
      if (
        sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        e.target !== toggleBtn
      ) {
        sidebar.classList.remove("open");
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) {
        sidebar.classList.remove("open");
        toggleBtn.style.display = "none";
      } else {
        toggleBtn.style.display = "flex";
      }
    });
  }

  /* ══════════════════════════════════════════════════════════
     6. TOAST NOTIFICATION SYSTEM
  ══════════════════════════════════════════════════════════ */
  window.SGAToast = {
    show(message, type = "info", duration = 4000) {
      const container =
        $(".toast-container") ||
        (() => {
          const c = document.createElement("div");
          c.className = "toast-container";
          document.body.appendChild(c);
          return c;
        })();

      const icons = {
        success: "check_circle",
        error: "error",
        warning: "warning",
        info: "info",
      };

      const colors = {
        success: "#10b981",
        error: "#ef4444",
        warning: "#f59e0b",
        info: "#13a4ec",
      };

      const toast = document.createElement("div");
      toast.className = `toast ${type}`;
      toast.innerHTML = `
        <span class="material-symbols-outlined" style="color:${colors[type]};font-size:1.2rem">${icons[type] || "info"}</span>
        <span style="flex:1;font-size:.875rem;font-family:var(--font)">${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;cursor:pointer;color:#94a3b8;font-size:1rem;padding:0">✕</button>
      `;
      container.appendChild(toast);

      if (duration > 0) {
        setTimeout(() => {
          toast.style.animation = "fadeUp 0.3s ease reverse";
          setTimeout(() => toast.remove(), 300);
        }, duration);
      }
    },
  };

  /* ══════════════════════════════════════════════════════════
     7. TABLE ROW HOVER RIPPLE
  ══════════════════════════════════════════════════════════ */
  function initTableRipple() {
    document.addEventListener("click", (e) => {
      const row = e.target.closest(".sga-table tbody tr");
      if (!row) return;

      const ripple = document.createElement("span");
      Object.assign(ripple.style, {
        position: "absolute",
        width: "6px", height: "6px",
        borderRadius: "50%",
        background: "rgba(19, 164, 236, 0.2)",
        transform: "scale(0)",
        animation: "pulseRing 0.6s ease-out forwards",
        pointerEvents: "none",
        left: `${e.offsetX}px`,
        top: `${e.offsetY}px`,
      });

      row.style.position = "relative";
      row.style.overflow = "hidden";
      row.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }

  /* ══════════════════════════════════════════════════════════
     8. FLOATING PARTICLES on login page
  ══════════════════════════════════════════════════════════ */
  function initLoginParticles() {
    const left = $(".login-left");
    if (!left) return;

    for (let i = 0; i < 8; i++) {
      const p = document.createElement("div");
      const size = Math.random() * 60 + 20;
      Object.assign(p.style, {
        position: "absolute",
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "50%",
        background: "rgba(255,255,255," + (Math.random() * 0.06 + 0.02) + ")",
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        backdropFilter: "blur(4px)",
        animation: `${Math.random() > 0.5 ? "floatA" : "floatB"} ${Math.random() * 4 + 5}s ${Math.random() * 3}s ease-in-out infinite`,
        pointerEvents: "none",
        zIndex: 1,
      });
      left.appendChild(p);
    }
  }

  /* ══════════════════════════════════════════════════════════
     9. SMOOTH PAGE TRANSITIONS (Dash navigation)
  ══════════════════════════════════════════════════════════ */
  function initPageTransitions() {
    const content = $("#page-content");
    if (!content) return;

    // Observe mutations (Dash re-renders content)
    const observer = new MutationObserver(() => {
      content.style.opacity = "0";
      content.style.transform = "translateY(8px)";
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          content.style.transition = "opacity 0.3s ease, transform 0.3s ease";
          content.style.opacity = "1";
          content.style.transform = "translateY(0)";
        });
      });
    });

    observer.observe(content, { childList: true, subtree: false });
  }

  /* ══════════════════════════════════════════════════════════
     10. INPUT FOCUS GLOW
  ══════════════════════════════════════════════════════════ */
  function initInputEffects() {
    document.addEventListener("focusin", (e) => {
      const el = e.target;
      if (
        el.matches(".sga-input, .sga-textarea, .sga-select") &&
        el.closest(".sga-card")
      ) {
        el.closest(".sga-card").style.boxShadow =
          "0 0 0 2px rgba(19, 164, 236, 0.08), 0 4px 16px rgba(0,0,0,.07)";
      }
    });

    document.addEventListener("focusout", (e) => {
      const el = e.target;
      if (
        el.matches(".sga-input, .sga-textarea, .sga-select") &&
        el.closest(".sga-card")
      ) {
        el.closest(".sga-card").style.boxShadow = "";
      }
    });
  }

  /* ══════════════════════════════════════════════════════════
     11. DASH CALLBACK OBSERVER – Re-run animations after updates
  ══════════════════════════════════════════════════════════ */
  function initDashObserver() {
    const observer = new MutationObserver(() => {
      animateCounters();
      animateProgressBars();
      initScrollAnimations();
      updateSidebarActive();
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  /* ══════════════════════════════════════════════════════════
     INIT – Wait for Dash to render
  ══════════════════════════════════════════════════════════ */
  function init() {
    initScrollAnimations();
    animateCounters();
    animateProgressBars();
    updateSidebarActive();
    initMobileSidebar();
    initTableRipple();
    initLoginParticles();
    initPageTransitions();
    initInputEffects();
    initDashObserver();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-init when Dash navigates
  window.addEventListener("popstate", () => {
    setTimeout(() => {
      updateSidebarActive();
      animateCounters();
    }, 200);
  });
})();
