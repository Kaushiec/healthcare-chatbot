
/*
  Healthcare Chatbot API Adapter
  Part 28, Step 28B

  Sends chat messages to the FastAPI backend.
  Manages the conversation session ID.
*/

async function sendHealthcareMessage(message, location = null) {

  // Retrieve the session ID from this browser tab.
  const sessionId = sessionStorage.getItem(
    "healthcare_session_id"
  );

  // Prepare the data that will be sent to FastAPI.
  const payload = {
    message: message,
    session_id: sessionId,
    location: location
  };

  // Send the message to your existing backend.
  const response = await fetch("/api/chat", {
    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify(payload)
  });

  // Convert the backend's JSON response to a JavaScript object.
  const data = await response.json();
  if (data === null || typeof data !== "object") {
  throw new Error(
    "Backend returned null instead of a chatbot response. Check process_chat() in chat_pipeline.py."
  );
 } 
  console.log("API RESPONSE:", data);
  console.log("ANSWER:", data.answer);
  console.log("STATUS:", data.status);
  console.log("RESULTS:", data.results);

  // Handle unsuccessful HTTP responses.
  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : `Backend returned HTTP ${response.status}`;

    throw new Error(detail);
  }

  // Check that the expected answer was returned.
  if (typeof data.answer !== "string") {
    throw new Error(
      "The backend response does not contain a valid answer."
    );
  }

  // Store the session ID if the backend provides one.
  if (typeof data.session_id === "string" && data.session_id) {
    sessionStorage.setItem(
      "healthcare_session_id",
      data.session_id
    );
  }

  // Return the complete response to script.js.
  return data;
}

