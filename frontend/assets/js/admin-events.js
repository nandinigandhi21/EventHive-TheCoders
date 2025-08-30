const API_BASE = "http://127.0.0.1:5000/api/admin";
const token = localStorage.getItem("token");

async function fetchEvents() {
  try {
    const res = await fetch(`${API_BASE}/events`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const data = await res.json();

    const tbody = document.getElementById("eventsTable");
    tbody.innerHTML = "";

    data.items.forEach(e => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="px-4 py-2">${e.id}</td>
        <td class="px-4 py-2">${e.title}</td>
        <td class="px-4 py-2">${e.category || "-"}</td>
        <td class="px-4 py-2">${e.date || "-"}</td>
        <td class="px-4 py-2">${e.location || "-"}</td>
        <td class="px-4 py-2">${e.status}</td>
        <td class="px-4 py-2">
          <button class="bg-blue-500 text-white px-2 py-1 rounded mr-2" onclick="toggleEvent(${e.id})">Toggle Status</button>
          <button class="bg-red-600 text-white px-2 py-1 rounded" onclick="deleteEvent(${e.id})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error fetching events:", err);
  }
}

async function toggleEvent(id) {
  await fetch(`${API_BASE}/events/${id}/toggle`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` }
  });

  fetchEvents();
}

async function deleteEvent(id) {
  if (!confirm("Are you sure you want to delete this event?")) return;

  await fetch(`${API_BASE}/events/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` }
  });

  fetchEvents();
}

fetchEvents();
