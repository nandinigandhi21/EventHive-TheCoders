// assets/js/attendee.js

let allEvents = [];
let currentPage = 1;
const perPage = 6; // how many events per page

// ---------- Render Event Cards ----------
function renderEvents(events) {
  const grid = document.getElementById("eventsGrid");

  if (!events.length) {
    grid.innerHTML = `
      <div class="col-span-full text-center text-gray-500 bg-white shadow rounded-lg p-8">
        No events found
      </div>`;
    document.getElementById("pagination").innerHTML = "";
    return;
  }

  grid.innerHTML = events.map(e => `
    <div 
      class="bg-white shadow rounded-xl overflow-hidden transform transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl cursor-pointer flex items-center justify-center"
      onclick="viewEvent(${e.id})"
    >
      <div class="p-3 text-center w-full h-45 flex flex-col justify-center">
        <h3 class="text-xl font-bold text-[#1E293B] mb-2">${e.title}</h3>
        <p class="text-sm text-gray-600 mb-1">${e.date} • ${e.location}</p>
        <p class="text-sm text-gray-500 mb-2 line-clamp-2">${e.description}</p>
        <span class="inline-block mt-2 text-sm ${e.ticket_type?.toLowerCase() === 'free' 
          ? 'bg-green-100 text-green-700' 
          : 'bg-yellow-100 text-yellow-700'} px-3 py-1 rounded-full">
          ${e.ticket_type || "General"}
        </span>
      </div>
    </div>
  `).join("");
}

// ---------- Render Pagination ----------
function renderPagination(totalItems) {
  const pagination = document.getElementById("pagination");
  const totalPages = Math.ceil(totalItems / perPage);
  if (totalPages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  pagination.innerHTML = `
    <button onclick="changePage(${currentPage - 1})" class="px-3 py-1 border rounded hover:bg-gray-100" ${currentPage === 1 ? "disabled" : ""}>&lt;</button>
    ${Array.from({ length: totalPages }, (_, i) => `
      <button onclick="changePage(${i + 1})" 
        class="px-3 py-1 border rounded ${currentPage === i + 1 ? "bg-[#2563EB] text-white" : "hover:bg-gray-100"}">
        ${i + 1}
      </button>
    `).join("")}
    <button onclick="changePage(${currentPage + 1})" class="px-3 py-1 border rounded hover:bg-gray-100" ${currentPage === totalPages ? "disabled" : ""}>&gt;</button>
  `;
}

function changePage(page) {
  currentPage = page;
  applyFilters();
}

// ---------- Fetch Events from Backend ----------
async function fetchEvents() {
  try {
    const res = await fetch("http://127.0.0.1:5000/api/events");

    if (!res.ok) throw new Error("Failed to fetch events");
    const data = await res.json();
    allEvents = data.items || data; // backend may return {items: []} or []

    applyFilters();
  } catch (err) {
    console.error("❌ Backend not ready, using fallback demo data", err);
    allEvents = [
      { id: 1, title: "AI Bootcamp", description: "Deep dive into ML & DL.", category: "workshops", date: "2025-09-12", time: "10:00 AM", location: "Bangalore", ticket_type: "Paid", price: 499 },
      { id: 2, title: "Music Fest", description: "Live music and food.", category: "music", date: "2025-09-20", time: "06:00 PM", location: "Mumbai", ticket_type: "Free", price: 0 },
      { id: 3, title: "City Marathon", description: "Run for a cause.", category: "sports", date: "2025-10-01", time: "07:00 AM", location: "Delhi", ticket_type: "Paid", price: 299 }
    ];
    applyFilters();
  }
}

// ---------- Apply Filters ----------
function applyFilters() {
  const category = document.getElementById("filterCategory").value.toLowerCase();
  const ticket = document.getElementById("filterTicket").value.toLowerCase();
  const search = document.getElementById("searchInput").value.toLowerCase();

  let filtered = allEvents.filter(e =>
    (!category || e.category?.toLowerCase() === category) &&
    (!ticket || e.ticket_type?.toLowerCase() === ticket) &&
    (e.title.toLowerCase().includes(search) || e.description.toLowerCase().includes(search))
  );

  // pagination slice
  const start = (currentPage - 1) * perPage;
  const paginated = filtered.slice(start, start + perPage);

  renderEvents(paginated);
  renderPagination(filtered.length);
}

// ---------- Card Click: Show Modal with Details ----------
async function viewEvent(id) {
  try {
    const res = await fetch(`http://127.0.0.1:5000/api/events/${id}`);
    if (!res.ok) throw new Error("Failed to fetch event details");

    const e = await res.json();

    document.getElementById("modalTitle").textContent = e.title;
    document.getElementById("modalDate").textContent = `📅 ${e.date} • ${e.time || "TBA"}`;
    document.getElementById("modalLocation").textContent = `📍 ${e.location}`;
    document.getElementById("modalDescription").textContent = e.description;
    document.getElementById("modalPrice").textContent = e.ticket_type?.toLowerCase() === "free" 
      ? "Free Entry" 
      : `₹${e.price}`;

    // set booking button
    const bookBtn = document.getElementById("bookBtn");
    bookBtn.onclick = () => {
      window.open(`book-tickets.html?eventId=${e.id}`, "_blank");
    };

    // show modal
    document.getElementById("eventModal").classList.remove("hidden");
    document.getElementById("eventModal").classList.add("flex");
  } catch (err) {
    console.error(err);
    alert("Unable to load event details");
  }
}

// ---------- Close Modal ----------
function closeModal() {
  document.getElementById("eventModal").classList.add("hidden");
  document.getElementById("eventModal").classList.remove("flex");
}

// ---------- Attach Listeners ----------
document.getElementById("filterCategory").addEventListener("change", () => { currentPage = 1; applyFilters(); });
document.getElementById("filterTicket").addEventListener("change", () => { currentPage = 1; applyFilters(); });
document.getElementById("searchInput").addEventListener("input", () => { currentPage = 1; applyFilters(); });

// ---------- Init ----------
fetchEvents();
