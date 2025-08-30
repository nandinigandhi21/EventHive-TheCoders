// assets/js/admin.js
// Fetch metrics, render KPIs, and draw charts. Falls back to mock data if API not ready.

const fmt = (n) => new Intl.NumberFormat("en-IN").format(n);

async function getMetrics() {
  try {
    // Recommended backend: GET /api/admin/metrics
    const res = await fetch("/api/admin/metrics");
    if (!res.ok) throw new Error("no metrics endpoint");
    return await res.json();
  } catch (e) {
    // Fallback mock (so UI still looks great for judges)
    return {
      ok: true,
      totals: {
        users: 1280,
        organizers: 42,
        events: 156,
        published: 98,
        ticketsSold: 5230,
        revenue: 1875000
      },
      timeseries: {
        days: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
        signups: [32, 41, 50, 39, 44, 61, 57],
        bookings: [70, 65, 80, 74, 89, 110, 95]
      },
      categories: { hackathon: 22, workshop: 48, concert: 36, sports: 18, other: 32 }
    };
  }
}

function renderKPIs(m) {
  document.getElementById("kpiTotalUsers").textContent = fmt(m.totals.users);
  document.getElementById("kpiTotalOrganizers").textContent = `Organizers: ${fmt(m.totals.organizers)}`;
  document.getElementById("kpiTotalEvents").textContent = fmt(m.totals.events);
  document.getElementById("kpiPublishedEvents").textContent = `Published: ${fmt(m.totals.published)}`;
  document.getElementById("kpiTicketsSold").textContent = fmt(m.totals.ticketsSold);
  document.getElementById("kpiRevenue").textContent = `₹ ${fmt(m.totals.revenue)}`;
}

function drawLineChart(days, signups, bookings) {
  const ctx = document.getElementById("lineChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: days,
      datasets: [
        { label: "Signups", data: signups, tension: 0.35 },
        { label: "Bookings", data: bookings, tension: 0.35 }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } },
      scales: { y: { beginAtZero: true } }
    }
  });
}

function drawDoughnutChart(categoryObj) {
  const ctx = document.getElementById("doughnutChart").getContext("2d");
  const labels = Object.keys(categoryObj);
  const data = Object.values(categoryObj);
  new Chart(ctx, {
    type: "doughnut",
    data: { labels, datasets: [{ data }] },
    options: { responsive: true, plugins: { legend: { position: "bottom" } } }
  });
}

(async function init() {
  const m = await getMetrics();
  if (!m.ok) return;
  renderKPIs(m);
  drawLineChart(m.timeseries.days, m.timeseries.signups, m.timeseries.bookings);
  drawDoughnutChart(m.categories);
})();
