let signalSent = false;
let requestInFlight = false;

function sendActivationSignal() {
  if (signalSent || requestInFlight) {
    return;
  }

  requestInFlight = true;

  fetch("http://127.0.0.1:5001/activate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ event: "password_detected" })
  })
    .then(() => {
      console.log("SafeLink AI: Signal sent successfully");
      signalSent = true;
    })
    .catch(() => {
      console.log("SafeLink AI: Failed to contact backend");
    })
    .finally(() => {
      requestInFlight = false;
    });
}

function checkPasswordFields() {
  const passwordFields = document.querySelectorAll('input[type="password"]');

  if (passwordFields.length > 0 && !signalSent) {
    console.log("SafeLink AI: Password field detected");
    sendActivationSignal();
  }
}

setInterval(checkPasswordFields, 2000);
checkPasswordFields();
