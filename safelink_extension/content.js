// Sends login-page trigger to local SafeLink AI server.
let lastTriggerTime = 0;
const TRIGGER_COOLDOWN_MS = 8000;
let pausedByUser = false;

function sendStartRequest() {
  if (pausedByUser) {
    return;
  }

  const now = Date.now();
  if (now - lastTriggerTime < TRIGGER_COOLDOWN_MS) {
    return;
  }

  lastTriggerTime = now;

  fetch("http://localhost:5000/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ source: "safelink_extension" })
  })
    .then((response) => response.json())
    .then((data) => {
      if (data && data.status === "stopped_by_user") {
        pausedByUser = true;
        console.log("SafeLink AI: Monitoring paused after Q. Run POST /resume to enable again.");
        return;
      }

      console.log("SafeLink AI: Trigger sent to local server");
    })
    .catch(() => {
      console.log("SafeLink AI: Could not contact local server");
    });
}

function checkLoginPasswordField() {
  const passwordField = document.querySelector("input[type='password']");
  if (passwordField) {
    sendStartRequest();
  }
}

// Check every 2 seconds as required.
setInterval(checkLoginPasswordField, 2000);
checkLoginPasswordField();
