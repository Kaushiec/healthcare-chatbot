
(function () {
    "use strict";

    function initializeNewChat() {

        const button =
            document.getElementById("newChatBtn");

        if (!button) {
            console.error(
                "New Chat: Button not found in HTML."
            );
            return;
        }

        console.log("New Chat button initialized.");

        button.addEventListener("click", function (event) {

            event.preventDefault();

            console.log("New Chat button clicked.");

            // Clear the current conversation session.
            sessionStorage.removeItem(
                "healthcare_session_id"
            );

            // Reload to clear displayed messages
            // and start a fresh conversation.
            window.location.reload();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeNewChat,
            { once: true }
        );
    } else {
        initializeNewChat();
    }

})();
