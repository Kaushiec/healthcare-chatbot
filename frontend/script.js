// This file matches index.html's element IDs exactly.
const messageInput = document.getElementById("searchInput");
const sendButton = document.getElementById("sendBtn");
const chatMessages = document.getElementById("chatMessages");
const suggestionButtons = document.querySelectorAll(".suggestion-chip");
const locationButton = document.getElementById("locationBtn");
const locationStatus = document.getElementById("locationStatus");

let userCoordinates = null; // Only filled after a user grants permission.
let sending = false;

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
});

suggestionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.textContent.trim();
    sendMessage();
  });
});

locationButton.addEventListener("click", getLocation);

function addMessage(text, sender) {
  const element = document.createElement("div");

  element.classList.add(
    "message",
    sender === "user" ? "user-message" : "bot-message"
  );

  element.textContent = text;

  chatMessages.appendChild(element);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  return element;
}


async function sendMessage() {

  // 1. Get the user's message from the existing search box.
  const message = messageInput.value.trim();

  // 2. Prevent empty messages or duplicate requests.
  if (!message || sending) {
    return;
  }

  // 3. Disable the send button while processing.
  sending = true;
  sendButton.disabled = true;

  // 4. Show the user's message in the chat.
  addMessage(message, "user");

  // 5. Clear the input box.
  messageInput.value = "";

  // 6. Include location only when it was permitted
  //    and the question specifically needs it.
  let locationForRequest = null;

  const isLocationQuery =
    /\b(near me|nearby|closest|around me|within \d+ ?km)\b/i.test(message);

  if (userCoordinates && isLocationQuery) {
    locationForRequest = userCoordinates;
  }

  try {

    // 7. Send the message through our NEW API adapter.
    const data = await sendHealthcareMessage(
      message,
      locationForRequest
    );

    // 8. Display the assistant's text response.
    const botBubble = addMessage(data.answer, "bot");

    // 9. Display structured result cards when available.
    if (typeof renderHealthcareResults === "function") {
      renderHealthcareResults(
        data.results,
        botBubble
      );
    }

    // 10. Scroll to show the latest chat content.
    chatMessages.scrollTop = chatMessages.scrollHeight;

  } catch (error) {

    // 11. Show errors in the console for debugging.
    console.error("Chat request failed:", error);

    // 12. Show a user-friendly error in the chat.
    addMessage(
      "Sorry, I couldn't process your request. Please try again.",
      "bot"
    );

  } finally {

    // 13. Re-enable the send button.
    sending = false;
    sendButton.disabled = false;

    // 14. Return keyboard focus to the input.
    messageInput.focus();
  }
}
function getLocation() {
  if (!navigator.geolocation) {
    locationStatus.textContent = "Your browser does not support geolocation.";
    return;
  }
  locationStatus.textContent = "Requesting location permission...";
  navigator.geolocation.getCurrentPosition(
    (position) => {
      userCoordinates = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude
      };
      locationStatus.textContent = "Location available for nearby searches.";
    },
    (error) => {
      userCoordinates = null;
      locationStatus.textContent = "Location not available. You can still search by city or area.";
      console.error("Geolocation error:", error);
    },
    { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
  );

}
