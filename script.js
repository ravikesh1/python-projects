const FARES = [
  // Vancouver (YVR) routes — Canada
  { airline: "Fiji Airways", code: "FJ", origin: "YVR", originCity: "Vancouver", dest: "NAN", destCity: "Nadi", price: 1180, duration: 900, stops: 0, depart: "11:35 PM", arrive: "8:20 AM +2", note: "Seasonal nonstop" },
  { airline: "Air Canada", code: "AC", origin: "YVR", originCity: "Vancouver", dest: "NAN", destCity: "Nadi", price: 1295, duration: 1080, stops: 1, depart: "10:45 PM", arrive: "9:15 AM +2", note: "via LAX" },
  { airline: "Fiji Airways", code: "FJ", origin: "YVR", originCity: "Vancouver", dest: "SUV", destCity: "Suva", price: 1420, duration: 1185, stops: 1, depart: "10:00 PM", arrive: "11:30 AM +2", note: "via NAN" },
  { airline: "WestJet + Fiji Airways", code: "WS", origin: "YVR", originCity: "Vancouver", dest: "NAN", destCity: "Nadi", price: 1340, duration: 1260, stops: 1, depart: "8:15 AM", arrive: "9:00 AM +2", note: "via LAX" },
  { airline: "United", code: "UA", origin: "YVR", originCity: "Vancouver", dest: "NAN", destCity: "Nadi", price: 1410, duration: 1395, stops: 2, depart: "6:30 AM", arrive: "1:45 PM +2", note: "via SFO, HNL" },

  // Toronto
  { airline: "Air Canada + Fiji Airways", code: "AC", origin: "YYZ", originCity: "Toronto", dest: "NAN", destCity: "Nadi", price: 1620, duration: 1530, stops: 1, depart: "9:45 PM", arrive: "9:15 AM +2", note: "via LAX" },
  { airline: "American Airlines", code: "AA", origin: "YYZ", originCity: "Toronto", dest: "NAN", destCity: "Nadi", price: 1745, duration: 1740, stops: 2, depart: "7:00 AM", arrive: "5:20 PM +2", note: "via DFW, LAX" },

  // Los Angeles
  { airline: "Fiji Airways", code: "FJ", origin: "LAX", originCity: "Los Angeles", dest: "NAN", destCity: "Nadi", price: 849, duration: 645, stops: 0, depart: "11:30 PM", arrive: "5:55 AM +2", note: "Daily nonstop" },
  { airline: "Fiji Airways", code: "FJ", origin: "LAX", originCity: "Los Angeles", dest: "SUV", destCity: "Suva", price: 1085, duration: 930, stops: 1, depart: "11:30 PM", arrive: "9:25 AM +2", note: "via NAN" },
  { airline: "American Airlines", code: "AA", origin: "LAX", originCity: "Los Angeles", dest: "NAN", destCity: "Nadi", price: 920, duration: 720, stops: 0, depart: "10:00 PM", arrive: "5:00 AM +2", note: "Codeshare with Fiji Airways" },

  // San Francisco
  { airline: "Fiji Airways", code: "FJ", origin: "SFO", originCity: "San Francisco", dest: "NAN", destCity: "Nadi", price: 899, duration: 665, stops: 0, depart: "10:35 PM", arrive: "5:40 AM +2", note: "3x weekly nonstop" },
  { airline: "United", code: "UA", origin: "SFO", originCity: "San Francisco", dest: "NAN", destCity: "Nadi", price: 1045, duration: 945, stops: 1, depart: "10:30 AM", arrive: "5:15 PM +1", note: "via HNL" },

  // Honolulu
  { airline: "Fiji Airways", code: "FJ", origin: "HNL", originCity: "Honolulu", dest: "NAN", destCity: "Nadi", price: 640, duration: 390, stops: 0, depart: "11:30 PM", arrive: "8:00 AM +2", note: "Daily nonstop" },
  { airline: "Hawaiian Airlines", code: "HA", origin: "HNL", originCity: "Honolulu", dest: "NAN", destCity: "Nadi", price: 695, duration: 410, stops: 0, depart: "1:20 PM", arrive: "8:30 PM +1", note: "3x weekly" },

  // Sydney
  { airline: "Fiji Airways", code: "FJ", origin: "SYD", originCity: "Sydney", dest: "NAN", destCity: "Nadi", price: 420, duration: 240, stops: 0, depart: "9:30 AM", arrive: "3:30 PM", note: "Multiple daily" },
  { airline: "Qantas", code: "QF", origin: "SYD", originCity: "Sydney", dest: "NAN", destCity: "Nadi", price: 465, duration: 245, stops: 0, depart: "1:15 PM", arrive: "7:20 PM", note: "Daily nonstop" },
  { airline: "Virgin Australia", code: "VA", origin: "SYD", originCity: "Sydney", dest: "NAN", destCity: "Nadi", price: 395, duration: 250, stops: 0, depart: "10:50 AM", arrive: "5:00 PM", note: "Codeshare" },

  // Melbourne
  { airline: "Fiji Airways", code: "FJ", origin: "MEL", originCity: "Melbourne", dest: "NAN", destCity: "Nadi", price: 510, duration: 290, stops: 0, depart: "8:30 AM", arrive: "3:20 PM", note: "Daily nonstop" },
  { airline: "Jetstar", code: "JQ", origin: "MEL", originCity: "Melbourne", dest: "NAN", destCity: "Nadi", price: 380, duration: 295, stops: 0, depart: "11:00 PM", arrive: "6:00 AM +1", note: "Low-cost" },

  // Brisbane
  { airline: "Fiji Airways", code: "FJ", origin: "BNE", originCity: "Brisbane", dest: "NAN", destCity: "Nadi", price: 445, duration: 215, stops: 0, depart: "11:55 AM", arrive: "5:30 PM", note: "Daily nonstop" },
  { airline: "Virgin Australia", code: "VA", origin: "BNE", originCity: "Brisbane", dest: "NAN", destCity: "Nadi", price: 410, duration: 225, stops: 0, depart: "3:10 PM", arrive: "8:55 PM", note: "Daily" },

  // Auckland
  { airline: "Fiji Airways", code: "FJ", origin: "AKL", originCity: "Auckland", dest: "NAN", destCity: "Nadi", price: 310, duration: 190, stops: 0, depart: "10:25 AM", arrive: "1:35 PM", note: "Multiple daily" },
  { airline: "Air New Zealand", code: "NZ", origin: "AKL", originCity: "Auckland", dest: "NAN", destCity: "Nadi", price: 345, duration: 195, stops: 0, depart: "1:45 PM", arrive: "5:00 PM", note: "Daily nonstop" },

  // Tokyo
  { airline: "Fiji Airways", code: "FJ", origin: "HND", originCity: "Tokyo", dest: "NAN", destCity: "Nadi", price: 1120, duration: 510, stops: 0, depart: "10:30 PM", arrive: "9:00 AM +1", note: "2x weekly" },
  { airline: "Japan Airlines", code: "JL", origin: "NRT", originCity: "Tokyo", dest: "NAN", destCity: "Nadi", price: 1280, duration: 740, stops: 1, depart: "6:25 PM", arrive: "9:30 AM +1", note: "via SYD" },

  // Hong Kong
  { airline: "Fiji Airways", code: "FJ", origin: "HKG", originCity: "Hong Kong", dest: "NAN", destCity: "Nadi", price: 985, duration: 580, stops: 0, depart: "11:55 PM", arrive: "11:35 AM +1", note: "2x weekly nonstop" },

  // Singapore
  { airline: "Fiji Airways", code: "FJ", origin: "SIN", originCity: "Singapore", dest: "NAN", destCity: "Nadi", price: 1050, duration: 645, stops: 0, depart: "11:15 PM", arrive: "1:00 PM +1", note: "Weekly nonstop" },
  { airline: "Singapore Airlines", code: "SQ", origin: "SIN", originCity: "Singapore", dest: "NAN", destCity: "Nadi", price: 1340, duration: 1020, stops: 1, depart: "8:30 AM", arrive: "5:30 PM +1", note: "via SYD" },

  // London
  { airline: "British Airways + Fiji Airways", code: "BA", origin: "LHR", originCity: "London", dest: "NAN", destCity: "Nadi", price: 1850, duration: 1620, stops: 1, depart: "9:55 AM", arrive: "5:55 PM +1", note: "via LAX" },
  { airline: "Qantas", code: "QF", origin: "LHR", originCity: "London", dest: "NAN", destCity: "Nadi", price: 1980, duration: 1740, stops: 1, depart: "10:30 AM", arrive: "9:30 AM +2", note: "via SIN, SYD" },
];

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const priceHistory = new Map();

function simulatePriceUpdate() {
  FARES.forEach((f, idx) => {
    const prev = f.price;
    const swing = Math.round((Math.random() - 0.48) * Math.max(20, f.price * 0.04));
    const next = Math.max(Math.round(f.price * 0.85), f.price + swing);
    priceHistory.set(idx, { prev, next });
    f.price = next;
  });
}

function updateTimestamp() {
  const el = document.getElementById("lastUpdated");
  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  el.textContent = `Live • updated ${time}`;
}

function flashRefresh() {
  const el = document.getElementById("lastUpdated");
  el.classList.add("refreshing");
  setTimeout(() => el.classList.remove("refreshing"), 800);
}

function formatDuration(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h ${m.toString().padStart(2, "0")}m`;
}

function stopsLabel(n) {
  if (n === 0) return "Nonstop";
  if (n === 1) return "1 stop";
  return `${n} stops`;
}

function populateSelects() {
  const origins = [...new Set(FARES.map((f) => f.origin))].sort();
  const originSelect = document.getElementById("origin");
  origins.forEach((code) => {
    const city = FARES.find((f) => f.origin === code).originCity;
    const opt = document.createElement("option");
    opt.value = code;
    opt.textContent = `${city} (${code})`;
    originSelect.appendChild(opt);
  });

  const airlines = [...new Set(FARES.map((f) => f.airline))].sort();
  const airlineSelect = document.getElementById("airline");
  airlines.forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    airlineSelect.appendChild(opt);
  });
}

function renderFares(fares) {
  const list = document.getElementById("fareList");
  const noResults = document.getElementById("noResults");
  const count = document.getElementById("resultCount");

  list.innerHTML = "";

  if (fares.length === 0) {
    noResults.hidden = false;
    count.textContent = "0 fares";
    return;
  }
  noResults.hidden = true;
  count.textContent = `${fares.length} fare${fares.length === 1 ? "" : "s"} found`;

  fares.forEach((f) => {
    const origIdx = FARES.indexOf(f);
    const history = priceHistory.get(origIdx);
    let deltaHtml = "";
    let priceClass = "";
    if (history && history.prev !== history.next) {
      const diff = history.next - history.prev;
      const dir = diff < 0 ? "down" : "up";
      const sign = diff < 0 ? "▼" : "▲";
      deltaHtml = `<span class="price-delta ${dir}">${sign} $${Math.abs(diff)}</span>`;
      priceClass = `price-${dir}`;
    }

    const card = document.createElement("article");
    card.className = "fare-card";
    card.innerHTML = `
      <div class="fare-main">
        <div class="airline-tag" title="${f.airline}">${f.code}</div>
        <div class="route">
          <div class="route-line">
            <span>${f.originCity} (${f.origin})</span>
            <span class="route-arrow">→</span>
            <span>${f.destCity} (${f.dest})</span>
          </div>
          <div class="route-meta">
            ${f.airline} • ${f.depart} → ${f.arrive} • ${formatDuration(f.duration)}
            ${f.note ? ` • ${f.note}` : ""}
          </div>
          <div class="stops stops-${f.stops}">${stopsLabel(f.stops)}</div>
        </div>
      </div>
      <div class="fare-price">
        <span class="price ${priceClass}">$${f.price.toLocaleString()}</span>
        <span class="price-unit">USD round-trip</span>
        ${deltaHtml}
        <button class="book-btn" type="button">View deal</button>
      </div>
    `;
    list.appendChild(card);
  });
}

function applyFilters() {
  const origin = document.getElementById("origin").value;
  const destination = document.getElementById("destination").value;
  const airline = document.getElementById("airline").value;
  const maxPrice = parseFloat(document.getElementById("maxPrice").value);
  const sort = document.getElementById("sort").value;

  let filtered = FARES.filter((f) => {
    if (origin && f.origin !== origin) return false;
    if (destination && f.dest !== destination) return false;
    if (airline && f.airline !== airline) return false;
    if (!isNaN(maxPrice) && f.price > maxPrice) return false;
    return true;
  });

  if (sort === "price") filtered.sort((a, b) => a.price - b.price);
  else if (sort === "duration") filtered.sort((a, b) => a.duration - b.duration);
  else if (sort === "stops") filtered.sort((a, b) => a.stops - b.stops || a.price - b.price);

  renderFares(filtered);
}

function resetFilters() {
  document.getElementById("origin").value = "";
  document.getElementById("destination").value = "";
  document.getElementById("airline").value = "";
  document.getElementById("maxPrice").value = "";
  document.getElementById("sort").value = "price";
  applyFilters();
}

document.addEventListener("DOMContentLoaded", () => {
  populateSelects();
  ["origin", "destination", "airline", "maxPrice", "sort"].forEach((id) => {
    document.getElementById(id).addEventListener("change", applyFilters);
    document.getElementById(id).addEventListener("input", applyFilters);
  });
  document.getElementById("reset").addEventListener("click", resetFilters);
  updateTimestamp();
  applyFilters();

  setInterval(() => {
    flashRefresh();
    simulatePriceUpdate();
    updateTimestamp();
    applyFilters();
  }, REFRESH_INTERVAL_MS);
});
