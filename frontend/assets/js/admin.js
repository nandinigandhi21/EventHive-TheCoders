async function getMetrics() {
  try {
    const res = await fetch("http://127.0.0.1:5001/api/admin/metrics", {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("token")}`
      }
    });
    if (!res.ok) throw new Error("metrics endpoint failed");
    const data = await res.json();

    return {
      ok: true,
      totals: {
        users: data.totals.users,
        organizers: data.totals.organizers,
        events: data.totals.events,
        published: data.totals.published,
        ticketsSold: data.totals.ticketsSold,
        revenue: data.totals.revenue
      },
      timeseries: data.timeseries,
      categories: data.categories
    };
  } catch (e) {
    console.error("Failed to fetch metrics:", e.message);
    return { ok: false };
  }
}

async function renderDashboard() {
  const metrics = await getMetrics();
  if (!metrics.ok) return;

  // Update KPIs
  document.getElementById("totalUsers").textContent = metrics.totals.users;
  document.getElementById("organizers").textContent = "Organizers: " + metrics.totals.organizers;
  document.getElementById("totalEvents").textContent = metrics.totals.events;
  document.getElementById("publishedEvents").textContent = "Published: " + metrics.totals.published;
  document.getElementById("ticketsSold").textContent = metrics.totals.ticketsSold;
  document.getElementById("revenue").textContent = "₹" + metrics.totals.revenue;

  // Charts
  const ctx1 = document.getElementById("signupsChart");
  new Chart(ctx1, {
    type: "line",
    data: {
      labels: metrics.timeseries.days,   // ✅ use correct field from backend
      datasets: [
        { label: "Signups", data: metrics.timeseries.signups, borderColor: "blue" },
        { label: "Bookings", data: metrics.timeseries.bookings, borderColor: "green" }
      ]
    }
  });

  const ctx2 = document.getElementById("categoryChart");
  new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: Object.keys(metrics.categories),
      datasets: [{ data: Object.values(metrics.categories) }]
    }
  });
}

// Run on load
renderDashboard();

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "login.html";
});
