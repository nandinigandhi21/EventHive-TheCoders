// assets/js/admin-users.js
// Fetch users, filter/search, promote roles, export CSV.
// Backend: GET /api/admin/users  |  PUT /api/admin/users/:id/role  |  DELETE /api/admin/users/:id

const API_BASE = "http://127.0.0.1:5000";  // 👈 Always call Flask server

let allUsers = [];

function roleBadge(role) {
  const map = {
    admin: "bg-rose-100 text-rose-700",
    organizer: "bg-emerald-100 text-emerald-700",
    attendee: "bg-sky-100 text-sky-700",
  };
  return `<span class="px-2 py-1 rounded text-xs ${map[role] || "bg-gray-100 text-gray-700"}">${role}</span>`;
}

function render(users) {
  const tbody = document.getElementById("usersTbody");
  tbody.innerHTML = users.map(u => `
    <tr class="border-t">
      <td class="p-3 font-medium">${u.username}</td>
      <td class="p-3">${u.email}</td>
      <td class="p-3">${u.phone || "-"}</td>
      <td class="p-3">${roleBadge(u.role)}</td>
      <td class="p-3 flex gap-2">
        <button class="px-3 py-1 rounded bg-emerald-600 text-white text-xs hover:opacity-90" onclick="setRole(${u.id}, 'organizer')">Make Organizer</button>
        <button class="px-3 py-1 rounded bg-rose-600 text-white text-xs hover:opacity-90" onclick="setRole(${u.id}, 'admin')">Make Admin</button>
        <button class="px-3 py-1 rounded bg-gray-200 text-gray-800 text-xs hover:opacity-90" onclick="removeUser(${u.id})">Delete</button>
      </td>
    </tr>
  `).join("");
}

async function fetchUsers() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/users`);
    if (!res.ok) throw new Error("no users endpoint");
    const data = await res.json();
    allUsers = data.items || data; // backend sends plain array
  } catch (err) {
    console.error("Failed to fetch users:", err);
    // Fallback demo data
    allUsers = [
      { id: 1, username: "Alice", email: "alice@mail.com", phone: "9999999999", role: "admin" },
      { id: 2, username: "Bob Org", email: "bob@mail.com", phone: "8888888888", role: "organizer" },
      { id: 3, username: "Charlie", email: "charlie@mail.com", phone: "7777777777", role: "attendee" }
    ];
  }
  render(allUsers);
}

async function setRole(id, role) {
  if (!confirm(`Change role to ${role}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/admin/users/${id}/role`, {
      method: "PUT", // 👈 fixed (was PATCH, backend accepts PUT)
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role })
    });
    if (!res.ok) throw 0;
    // Update locally
    allUsers = allUsers.map(u => u.id === id ? { ...u, role } : u);
    render(allUsers);
  } catch {
    alert("Failed to update role (ensure backend route exists).");
  }
}

async function removeUser(id) {
  if (!confirm("Delete this user? This cannot be undone.")) return;
  try {
    const res = await fetch(`${API_BASE}/api/admin/users/${id}`, { method: "DELETE" });
    if (!res.ok) throw 0;
    allUsers = allUsers.filter(u => u.id !== id);
    render(allUsers);
  } catch {
    alert("Failed to delete user (ensure backend route exists).");
  }
}

function attachFilters() {
  const searchInput = document.getElementById("searchInput");
  const roleFilter = document.getElementById("roleFilter");
  const exportBtn = document.getElementById("exportBtn");

  function apply() {
    const q = (searchInput.value || "").toLowerCase();
    const role = roleFilter.value;
    const filtered = allUsers.filter(u => {
      const matchQ = [u.username, u.email, u.phone].join(" ").toLowerCase().includes(q);
      const matchRole = !role || u.role === role;
      return matchQ && matchRole;
    });
    render(filtered);
  }

  searchInput.addEventListener("input", apply);
  roleFilter.addEventListener("change", apply);

  exportBtn.addEventListener("click", () => {
    const rows = [["Username","Email","Phone","Role"], ...allUsers.map(u => [u.username,u.email,u.phone || "",u.role])];
    const csv = rows.map(r => r.map(x => `"${String(x).replace(/"/g,'""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "users.csv"; a.click();
    URL.revokeObjectURL(url);
  });
}

fetchUsers();
attachFilters();
