async function checkBackend() {

    try {

        const response = await fetch("/api/health");

        const data = await response.json();

        document.getElementById("status").textContent =
            data.message;

    } catch (error) {

        document.getElementById("status").textContent =
            "Unable to connect to backend.";

        console.error(error);
    }
}


checkBackend();