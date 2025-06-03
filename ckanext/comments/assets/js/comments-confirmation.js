$(document).ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (token) {
        $.ajax({
            url: `/api/confirm_comment/${token}`,
            method: 'GET',
            success: function(response) {
                alert("Ihr Kommentar wurde gespeichert, und muss noch vom MobiData BW Team freigegeben werden.");
            },
            error: function(xhr, status, error) {
                alert("Fehler bei der Bestätigung des Kommentars.");
            }
        });
    }
});