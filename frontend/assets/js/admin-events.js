// assets/js/admin-events.js
// Manage events: fetch, filter/search, publish toggle, delete

const API_BASE = "http://127.0.0.1:5000";

let allEvents = [];

// Utility to get headers with token
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
}

function statusPill(status) {
  const cl =
    status === "published"
      ? "bg-emerald-100 text-emerald-700"
      : "bg-amber-100 text-amber-700";
  return `<span class="px-2 py-1 rounded text-xs ${cl}">${status}</span>`;
}

function card(e) {
  return `
  <article class="bg-white rounded-xl shadow p-5 flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">${e.title}</h3>
        ${statusPill(e.status)}
      </div>
      <p class="text-sm text-slate-500 mt-1 line-clamp-2">${e.description}</p>
      <div class="mt-3 text-sm grid grid-cols-2 gap-y-1">
        <p><span class="text-slate-400">Category:</span> ${e.category}</p>
        <p><span class="text-slate-400">Ticket:</span> ${e.ticket_type}</p>
        <p><span class="text-slate-400">Date:</span> ${e.date}</p>
        <p><span class="text-slate-400">Time:</span> ${e.time}</p>
        <p class="col-span-2"><span class="text-slate-400">Location:</span> ${e.location}</p>
      </div>
    </div>

    <div class="mt-4 flex gap-2">
      <button class="px-3 py-2 rounded bg-[#7A5C42] text-white text-xs hover:opacity-90" onclick="toggle(${e.id})">
        ${e.status === "published" ? "Unpublish" : "Publish"}
      </button>
      <a class="px-3 py-2 rounded bg-gray-100 text-gray-800 text-xs hover:opacity-90" href="organizer-edit.html?eventId=${e.id}">Edit</a>
      <button class="px-3 py-2 rounded bg-rose-600 text-white text-xs hover:opacity-90" onclick="removeEvent(${e.id})">Delete</button>
    </div>
  </article>
  `;
}

function render(list) {
  const wrap = document.getElementById("eventsWrap");
  if (!list.length) {
    wrap.innerHTML = `
      <div class="col-span-full bg-white rounded-xl shadow p-8 text-center text-slate-500">
        No events match your filters.
      </div>`;
    return;
  }
  wrap.innerHTML = list.map(card).join("");
}

async function fetchEvents() {
  const status = document.getElementById("statusFilter").value;
  const category = document.getElementById("categoryFilter").value;

  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (category) params.set("category", category);
  params.set("limit", 100);

  try {
    const res = await fetch(`${API_BASE}/api/events?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error("Failed to fetch events");
    const data = await res.json();
    allEvents = data.items || [];
  } catch (err) {
    console.warn("Using fallback demo data:", err.message);
    allEvents = [
      { id: 1, title: "AI Bootcamp", description: "Deep dive into ML & DL.", category: "workshop", date:"2025-10-02", time:"10:00 AM", location:"Bengaluru", ticket_type:"General", status:"published" },
      { id: 2, title: "City Marathon", description: "5k, 10k, Half Marathon", category: "sports", date:"2025-09-10", time:"6:00 AM", location:"Mumbai", ticket_type:"General", status:"draft" },
      { id: 3, title: "Hack the Future", description: "48h Hackathon", category: "hackathon", date:"2025-12-01", time:"9:00 AM", location:"Delhi", ticket_type:"Early Bird", status:"published" }
    ];
  }
  applyFilters();
}

function applyFilters() {
  const q = (document.getElementById("searchEvent").value || "").toLowerCase();
  const filtered = allEvents.filter(e =>
    (e.title + " " + e.description).toLowerCase().includes(q)
  );
  render(filtered);
}

async function toggle(eventId) {
  try {
    const res = await fetch(`${API_BASE}/api/events/${eventId}/toggle`, {
      method: "PATCH",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error();
    // update local state
    allEvents = allEvents.map(e =>
      e.id === eventId
        ? { ...e, status: e.status === "published" ? "draft" : "published" }
        : e
    );
    applyFilters();
  } catch {
    alert("Failed to toggle status (check backend route & auth).");
  }
}

async function removeEvent(eventId) {
  if (!confirm("Delete this event?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/events/${eventId}`, {
      method: "DELETE",
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error();
    allEvents = allEvents.filter(e => e.id !== eventId);
    applyFilters();
  } catch {
    alert("Failed to delete event (check backend route & auth).");
  }
}

// Event listeners
document.getElementById("refreshBtn").addEventListener("click", fetchEvents);
document.getElementById("statusFilter").addEventListener("change", fetchEvents);
document.getElementById("categoryFilter").addEventListener("change", fetchEvents);
document.getElementById("searchEvent").addEventListener("input", applyFilters);

// Initial load
fetchEvents();
