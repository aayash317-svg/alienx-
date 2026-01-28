// TEMP until login/JWT is wired
const PATIENT_ID = prompt("Enter your Patient ID:");

fetch("/admin/register_patient_and_card", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        name: "TEMP",
        phone: "TEMP",
        blood_group: "TEMP",
        emergency_contact: "TEMP"
    })
})
.then(res => res.json())
.then(data => {
    document.getElementById("qr").src = "/" + data.qr_image_path;
    document.getElementById("payload").innerText =
        "NFC Payload:\n" + data.card_payload;
});
