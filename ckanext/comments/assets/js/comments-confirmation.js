$(document).ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
        $.ajax({
            url: `/api/confirm_comment/${token}`,
            method: 'GET',
            success: function(response) {
                alert("Kommentar erfolgreich gespeichert!");
                // Optional: Weiterleitung oder Anzeige einer Bestätigungsmeldung
            },
            error: function(xhr, status, error) {
                alert("Fehler bei der Bestätigung des Kommentars.");
            }
        });
    }
});