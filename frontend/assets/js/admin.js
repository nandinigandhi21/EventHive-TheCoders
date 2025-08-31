// assets/js/admin.js
const API_BASE = "http://127.0.0.1:5000/api/admin";
const token = localStorage.getItem("token");

async function getMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("metrics endpoint failed");
    return await res.json();
  } catch (e) {
    console.error("Failed to fetch metrics:", e.message);
    return { ok: false };
  }
}

async function renderDashboard() {
  const metrics = await getMetrics();
  if (!metrics.ok) return;

  // KPIs
  document.getElementById("totalUsers").textContent = metrics.totals.users;
  document.getElementById("organizers").textContent =
    "Organizers: " + metrics.totals.organizers;
  document.getElementById("totalEvents").textContent = metrics.totals.events;
  document.getElementById("publishedEvents").textContent =
    "Published: " + metrics.totals.published;
  document.getElementById("ticketsSold").textContent =
    metrics.totals.ticketsSold;
  document.getElementById("revenue").textContent = "₹" + metrics.totals.revenue;

  // Charts
  const ctx1 = document.getElementById("signupsChart");
  new Chart(ctx1, {
    type: "line",
    data: {
      labels: metrics.timeseries.days,
      datasets: [
        {
          label: "Signups",
          data: metrics.timeseries.signups,
          borderColor: "blue",
        },
        {
          label: "Bookings",
          data: metrics.timeseries.bookings,
          borderColor: "green",
        },
      ],
    },
  });

  const ctx2 = document.getElementById("categoryChart");
  new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: Object.keys(metrics.categories),
      datasets: [{ data: Object.values(metrics.categories) }],
    },
  });
}

renderDashboard();

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "login.html";
});
