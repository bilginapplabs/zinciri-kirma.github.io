// Zinciri Kırma website: small touches only; every page works without this file.
(function () {
  var top = document.querySelector(".top");
  function onScroll() {
    if (top) top.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Today's link closes once the week comes into view.
  var week = document.querySelector(".week");
  if (week && "IntersectionObserver" in window) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          week.classList.add("play");
          seen.disconnect();
        }
      });
    }, { threshold: 0.6 });
    seen.observe(week);
  } else if (week) {
    week.classList.add("play");
  }

  // Screenshot arrows move by one image.
  var shots = document.querySelector(".shots");
  document.querySelectorAll("[data-shots]").forEach(function (b) {
    b.addEventListener("click", function () {
      var fig = shots && shots.querySelector("figure");
      if (!fig) return;
      var step = fig.getBoundingClientRect().width + 18;
      shots.scrollBy({ left: step * Number(b.getAttribute("data-shots")), behavior: "smooth" });
    });
  });

  // The contents list follows the section being read.
  var toc = document.querySelectorAll(".toc a");
  if (toc.length && "IntersectionObserver" in window) {
    var byId = {};
    toc.forEach(function (a) {
      byId[a.getAttribute("href").slice(1)] = a;
    });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        toc.forEach(function (a) {
          a.classList.remove("on");
        });
        var a = byId[e.target.id];
        if (a) a.classList.add("on");
      });
    }, { rootMargin: "-90px 0px -70% 0px" });
    document.querySelectorAll(".prose h2[id]").forEach(function (h) {
      spy.observe(h);
    });
  }
})();
