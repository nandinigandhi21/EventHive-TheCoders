const API_BASE = "http://127.0.0.1:5000/api/admin";
const token = localStorage.getItem("token");

async function fetchUsers() {
  try {
    const res = await fetch(`${API_BASE}/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const users = await res.json();

    const tbody = document.getElementById("usersTable");
    tbody.innerHTML = "";

    users.forEach(u => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="px-4 py-2">${u.id}</td>
        <td class="px-4 py-2">${u.username}</td>
        <td class="px-4 py-2">${u.email}</td>
        <td class="px-4 py-2">${u.phone || "-"}</td>
        <td class="px-4 py-2">${u.role}</td>
        <td class="px-4 py-2">
          <button class="bg-yellow-500 text-white px-2 py-1 rounded mr-2" onclick="changeRole(${u.id}, '${u.role}')">Change Role</button>
          <button class="bg-red-600 text-white px-2 py-1 rounded" onclick="deleteUser(${u.id})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error fetching users:", err);
  }
}

async function changeRole(id, currentRole) {
  const newRole = prompt("Enter new role (user/organizer/admin):", currentRole);
  if (!newRole) return;

  await fetch(`${API_BASE}/users/${id}/role`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ role: newRole })
  });

  fetchUsers();
}

async function deleteUser(id) {
  if (!confirm("Are you sure you want to delete this user?")) return;

  await fetch(`${API_BASE}/users/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` }
  });

  fetchUsers();
}

fetchUsers();
