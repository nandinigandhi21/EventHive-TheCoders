// assets/js/admin-users.js
const API_BASE = "http://127.0.0.1:5000/api/admin"; // keep this consistent with your backend port
const token = localStorage.getItem("token");

// -----------------------------
// Fetch + Render Users
// -----------------------------
async function fetchUsers() {
  const tbody = document.getElementById("usersTable"); // MUST match admin-users.html
  if (!tbody) {
    console.error('❌ <tbody id="usersTable"> not found in DOM.');
    return;
  }

  // Show loading state
  tbody.innerHTML = `
    <tr><td colspan="6" class="px-4 py-3 text-center text-gray-500">Loading users…</td></tr>
  `;

  try {
    const res = await fetch(`${API_BASE}/users`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json"
      }
    });

    const raw = await res.text(); // read raw first so we can log in case of non-JSON
    let data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      console.error("❌ /users returned non-JSON:", raw);
      tbody.innerHTML = `
        <tr><td colspan="6" class="px-4 py-3 text-center text-red-600">Failed to parse server response.</td></tr>
      `;
      return;
    }

    if (!res.ok) {
      console.error("❌ /users failed:", res.status, data);
      tbody.innerHTML = `
        <tr><td colspan="6" class="px-4 py-3 text-center text-red-600">Failed to fetch users (${res.status}).</td></tr>
      `;
      return;
    }

    // Support BOTH shapes: [] or { items: [] }
    const users = Array.isArray(data) ? data : (Array.isArray(data.items) ? data.items : []);

    if (!users.length) {
      tbody.innerHTML = `
        <tr><td colspan="6" class="px-4 py-3 text-center text-gray-500">No users found.</td></tr>
      `;
      return;
    }

    // Render rows
    tbody.innerHTML = "";
    users.forEach((u) => {
      // Your backend uses "username" (not "name") in earlier code; stay consistent.
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="px-4 py-2">${u.id}</td>
        <td class="px-4 py-2">${u.username ?? "-"}</td>
        <td class="px-4 py-2">${u.email ?? "-"}</td>
        <td class="px-4 py-2">${u.phone ?? "-"}</td>
        <td class="px-4 py-2">${u.role ?? "user"}</td>
        <td class="px-4 py-2">
          <button class="bg-yellow-500 text-white px-2 py-1 rounded mr-2"
            onclick="changeRole(${u.id}, '${u.role ?? "user"}')">Change Role</button>
          <button class="bg-red-600 text-white px-2 py-1 rounded"
            onclick="deleteUser(${u.id})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("❌ Network/JS error while fetching users:", err);
    tbody.innerHTML = `
      <tr><td colspan="6" class="px-4 py-3 text-center text-red-600">Error loading users.</td></tr>
    `;
  }
}

// -----------------------------
// Actions (exposed globally for inline onclick)
// -----------------------------
async function changeRole(id, currentRole) {
  const newRole = prompt("Enter new role (user/organizer/admin):", currentRole);
  if (!newRole) return;

  try {
    const res = await fetch(`${API_BASE}/users/${id}/role`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ role: newRole }),
    });
    if (!res.ok) {
      const txt = await res.text();
      console.error("❌ Failed to change role:", res.status, txt);
      alert("Failed to change role.");
      return;
    }
    await fetchUsers();
  } catch (e) {
    console.error("❌ Error changing role:", e);
  }
}

async function deleteUser(id) {
  if (!confirm("Are you sure you want to delete this user?")) return;

  try {
    const res = await fetch(`${API_BASE}/users/${id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    });
    if (!res.ok) {
      const txt = await res.text();
      console.error("❌ Failed to delete user:", res.status, txt);
      alert("Failed to delete user.");
      return;
    }
    await fetchUsers();
  } catch (e) {
    console.error("❌ Error deleting user:", e);
  }
}

// Make functions available to inline onclick handlers
window.changeRole = changeRole;
window.deleteUser = deleteUser;

// Init
document.addEventListener("DOMContentLoaded", fetchUsers);
