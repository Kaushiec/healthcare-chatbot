
function renderHealthcareResults(results, botBubble) {

  // Do nothing if there are no usable results.
  if (
    !botBubble ||
    !Array.isArray(results) ||
    results.length === 0
  ) {
    return;
  }

  // Avoid duplicate cards if this function runs twice.
  botBubble.querySelector(".healthcare-results")?.remove();

  // Create a container within the assistant's chat bubble.
  const container = document.createElement("div");
  container.className = "healthcare-results";

  const heading = document.createElement("p");
  heading.className = "healthcare-results-heading";
  heading.textContent = `Search results (${results.length})`;
  container.appendChild(heading);

  // Limit the initial display to 10 records.
  for (const record of results.slice(0, 10)) {

    if (!record || typeof record !== "object") {
      continue;
    }

    const card = document.createElement("article");
    card.className = "healthcare-result-card";

    const hospitalName = record.hospital_name || record.name;

    // Choose a suitable title for different result types.
    const titleText =
      record.doctor_name ||
      record.service_name ||
      record.bed_type ||
      hospitalName ||
      record.facility_name ||
      "Healthcare result";

    const title = document.createElement("h3");
    title.textContent = titleText;
    card.appendChild(title);

    // Helper: safely add one detail to a card.
    function addDetail(label, value) {
      if (value === null || value === undefined || value === "") {
        return;
      }

      const line = document.createElement("p");
      const labelElement = document.createElement("strong");

      labelElement.textContent = `${label}: `;
      line.appendChild(labelElement);
      line.appendChild(document.createTextNode(String(value)));

      card.appendChild(line);
    }

    // Show available database fields.
    if (hospitalName !== titleText) {
      addDetail("Hospital", hospitalName);
    }

    addDetail("City", record.city);
    addDetail("Address", record.address);
    addDetail("Phone", record.phone);

    addDetail("Department", record.department_name);
    addDetail("Facility", record.facility_name);
    addDetail("Specialization / Department", record.specialization);
    addDetail("Bed type", record.bed_type === titleText ? null : record.bed_type);

    addDetail("Reported beds", record.reported_bed_count);

    if (record.consultation_fee != null) {
      addDetail("Consultation fee", `₹${record.consultation_fee}`);
    }

    if (record.price_min != null) {
      addDetail("Minimum listed charge", `₹${record.price_min}`);
    }

    if (record.price_max != null) {
      addDetail("Maximum listed charge", `₹${record.price_max}`);
    }

    addDetail("Charge unit", record.fee_unit || record.price_unit);

    if (record.distance_km != null) {
      addDetail(
        "Straight-line distance",
        `${record.distance_km} km`
      );
    }

    
    // Make missing tariff verification dates explicit.
    if (
      record.last_verified != null &&
      record.last_verified !== ""
    ) {
      addDetail(
        "Last verified",
        record.last_verified
      );

    } else if (
      record.service_name &&
      (
        record.price_min != null ||
        record.price_max != null
      )
    ) {
      addDetail(
        "Price verification",
        "Verification date unavailable"
      );
    }

    addDetail("Source document", record.source_document);

    if (
      record.consultation_fee != null ||
      record.price_min != null ||
      record.price_max != null
    ) {
      const note = document.createElement("p");
      note.className = "healthcare-price-note";
      note.textContent =
        "Listed charge. Confirm the current price with the hospital.";
      card.appendChild(note);
    }

    if (record.emergency_24x7 === 1 ||
    record.emergency_24x7 === true) {
    addDetail("Emergency services", "Listed as 24x7");
    }

    if (record.ambulance_24x7 === 1 ||
    record.ambulance_24x7 === true) {
    addDetail("Ambulance", "Listed as 24x7");
    }

    container.appendChild(card);
  }

  if (results.length > 10) {
    const more = document.createElement("p");
    more.className = "healthcare-results-more";
    more.textContent =
      `Showing the first 10 of ${results.length} results.`;
    container.appendChild(more);
  }

  // Expand only this particular assistant bubble.
  botBubble.classList.add("with-results");

  // Place the result cards directly below the answer.
  botBubble.appendChild(container);
}
