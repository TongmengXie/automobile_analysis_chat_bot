async function sendMessage() {
    const input = document.getElementById("input");
    const chat = document.getElementById("chat");

    const text = input.value;
    if (!text) return;

    chat.innerHTML += `<div><b>You:</b> ${text}</div>`;

    const res = await fetch("/api/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text})
    });

    const data = await res.json();

    // chat.innerHTML += `<div><b>Assistant:</b> ${data.response}</div>`;
    chat.innerHTML += `<div><b>Assistant:</b> ${marked.parse(data.response)}</div>`;
    input.value = "";
}
