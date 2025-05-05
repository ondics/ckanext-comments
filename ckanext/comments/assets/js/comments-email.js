document.getElementById('save-button').addEventListener('click', function() {
    // Zeige das Modal
    $('#emailModal').modal('show');
  });
  
  document.getElementById('confirm-email').addEventListener('click', function() {
    // Hole die eingegebene E-Mail-Adresse
    var email = document.getElementById('authoremail').value;
    var name = document.getElementById('authorid').value;
    console.log("############################################ Bestätigungs-Button geklickt, eingegebene E-Mail: ", email);
    // E-Mail validieren
    if (validateEmail(email)) {
      console.log("########################################## E-Mail validiert: ", email);
      // E-Mail ist gültig, speichere sie im versteckten Feld
      document.getElementById('author_email').value = email;
      document.getElementById('author_id').value = name;
  
      // Modal schließen
      $('#emailModal').modal('hide');
  
      console.log("############################################ Formular wird gesendet");
      // Originalformular absenden
      document.getElementById('main-form').submit();
    } else {
      alert('Bitte geben Sie eine gültige E-Mail-Adresse ein.');
    }
  });
  
  function validateEmail(email) {
    var re = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$/;
    return re.test(String(email).toLowerCase());
  }