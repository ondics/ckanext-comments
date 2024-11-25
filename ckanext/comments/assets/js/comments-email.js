document.getElementById('save-button').addEventListener('click', function() {
    // Zeige das Modal
    $('#emailModal').modal('show');
  });
  
  document.getElementById('confirm-email').addEventListener('click', function() {
    // Hole die eingegebene E-Mail-Adresse
    var email = document.getElementById('authoremail').value;
    console.log("############################################ Bestätigungs-Button geklickt, eingegebene E-Mail: ", email);
    // E-Mail validieren
    if (validateEmail(email)) {
      console.log("########################################## E-Mail validiert: ", email);
      // E-Mail ist gültig, speichere sie im versteckten Feld
      document.getElementById('author_email').value = email;
  
      // Modal schließen
      $('#emailModal').modal('hide');
  
      // document.getElementById('main-form').addEventListener('submit', function(event) {
      //   event.preventDefault(); // Stoppt das Standardformular-Verhalten
      //   return false;
      // });
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