ckan.module("comments-thread", function ($) {
  "use strict";

  // Modulinstanz speichern
  return {
    options: {
      subjectId: null,
      subjectType: null,
      ajaxReload: null,
    },
    initialize: function () {
      // Hier sicherstellen, dass jQuery funktioniert
      if (typeof $ !== "function") {
        console.error("jQuery is not defined");
        return;
      }
      $.proxyAll(this, /_on/);
      this.$(".comment-actions .remove-comment").on(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").on(
        "click",
        this._onApproveComment
      );
      this.$(".comment-actions .reply-to-comment").on(
        "click",
        this._onReplyToComment
      );
      this.$(".comments-confirm-email").on(
        "click",
        this._onConfirmEmail
      );
      this.$(".comment-actions .edit-comment").on("click", this._onEditComment);
      this.$(".comment-actions .save-comment").on("click", this._onSaveComment);
      this.$(".comment-footer").on("click", this._onFooterClick);
      // Hier den Event-Listener für den Save-Button hinzufügen
      this.$("#save-button").on("click", this._onSaveButtonClick.bind(this)); // den Save-Button binden

      this.$("#confirm-pin").on("click", this._onConfirmPin.bind(this));
      this.$(".save-reply").on('click', this._onReplySave.bind(this));
      this.$("#confirm-reply-pin").on('click', this._onConfirmReplyPin.bind(this));
      this.$(".comment-form").on("submit", this._onSubmit.bind(this)); // bind the submit handler

      this.$(".close").on('click', function () {
        $('.modal').modal('hide');
      });
    },

    teardown: function () {
      this.$(".comment-action.remove-comment").off(
        "click",
        this._onRemoveComment
      );
      this.$(".comment-actions .approve-comment").off(
        "click",
        this._onApproveComment
      );

      this.$("#save-button").off("click", this._onSaveButtonClick.bind(this)); // hier auch entfernen

      this.$(".comment-form").off("submit", this._onSubmit);
    },
    _onSaveButtonClick: function (e) {
      e.preventDefault(); // Verhindere das Standardverhalten des Buttons
      // Öffne das Modal für die E-Mail-Eingabe
      $('#emailModal').modal('show'); 
    },
    // _onConfirmEmail: function (e) {
    //   const email = $('#authoremail').val(); // E-Mail von der Eingabe im Modal
    //   if (!this._isValidEmail(email)) {
    //     alert("Bitte geben Sie eine gültige E-Mail-Adresse ein.");
    //     return;
    //   }
    //   $('#author_email').val(email); // E-Mail im versteckten Feld des Formulars setzen
    //   $('#emailModal').modal('hide'); // Schließe das Modal

    //   // Jetzt das ursprüngliche Formular absenden
    //   const formElement = document.getElementById("main-form");
    //   const data = new FormData(formElement); // FormData direkt vom Form-Element erstellen
    //   this._saveComment({ content: data.get("content"), author_email: data.get("author_email"), create_thread: true });
    // },

    _onConfirmEmail: function (e) {
      e.preventDefault();
    
      const email = $('#authoremail').val(); // E-Mail von der Eingabe im Modal
      const name = $('#guestuser').val(); // Nutzername von der Eingabe im Modal
      if (!this._isValidEmail(email)) {
        alert("Bitte geben Sie eine gültige E-Mail-Adresse ein.");
        return;
      }
    
      // Fordere eine PIN vom Server an
      $.ajax({
        url: '/api/request_pin', // API-Endpunkt, der die PIN generiert und sendet
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ email, name }), // E-Mail an den Server senden
        success: function () {
          $('#emailModal').modal('hide'); // Schließe das E-Mail-Modal
          $('#pinModal').modal('show'); // Zeige das PIN-Modal an
          $('#author_email').val(email); // Setze die E-Mail im versteckten Feld
          $('#guest_user').val(name); // Setze die E-Mail im versteckten Feld
        },
        error: function () {
          alert('Fehler beim Anfordern der PIN. Bitte versuchen Sie es erneut.');
        }
      });
      
    },

    _onConfirmReplyPin: function (e) {
      e.preventDefault();
      const pin = $('#reply-pin-input').val(); // PIN aus dem Modal
      if (!pin || pin.length !== 6) {
        alert("Bitte geben Sie einen gültigen 6-stelligen PIN ein.");
        return;
      }
    
      const { content, email, name, reply_to_id } = this.e; // Gespeicherte Daten
    
      // PIN validieren und Reply speichern
      $.ajax({
        url: '/api/verify_pin',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ email, name, pin }),
        success: function () {
          // PIN bestätigt - Reply speichern
          this._saveComment({
            content: content,
            author_email: email,
            guest_user: name,
            reply_to_id: reply_to_id
          });
      
          // Modal schließen und Cleanup
          $('#replyPinModal').modal('hide');
          // this.e = null;
        }.bind(this),
        error: function () {
          alert("PIN ungültig oder abgelaufen. Bitte versuchen Sie es erneut.");
        }
      });
    },

    _onReplySave: function (e) {
      // PIN anfordern für die angegebene E-Mail-Adresse
      $.ajax({
        url: "/api/request_pin",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ email: e.email }),
        success: function () {
          console.log("PIN erfolgreich versendet an:", e.email);
          
          // Daten für spätere Speicherung merken
          this.e = e;
    
          // PIN-Eingabemodal öffnen
          $("#replyPinModal").modal("show");
        }.bind(this),
        error: function () {
          console.error("Fehler beim Senden der PIN.");
          alert("Die PIN konnte nicht gesendet werden. Bitte versuchen Sie es erneut.");
        },
      });
    },
    
    
    // Funktion für die PIN-Bestätigung
    _onConfirmPin: function (e) {
      e.preventDefault();
    
      const pin = $('#pin-input').val(); // Eingabe aus dem PIN-Feld
      const email = $('#author_email').val(); // Bereits gespeicherte E-Mail im Formular
      const name = $('#guest_user').val(); // Bereits gespeicherte E-Mail im Formular
      const formElement = document.getElementById("main-form");
    
      // Überprüfe die PIN auf dem Server
      $.ajax({
        url: '/api/verify_pin',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ pin, email, name }), // Sende PIN und E-Mail
        success: (response) => {
          // Wenn die PIN korrekt ist, speichere den Kommentar
          const data = new FormData(formElement); // Hole Formulardaten
          this._saveComment({
            content: data.get("content"),
            author_email: data.get("author_email"),
            guest_user: data.get("guest_user"),
            create_thread: true,
          });
          $('#pinModal').modal('hide'); // Schließe das PIN-Modal
          alert('Kommentar erfolgreich gespeichert!');
        },
        error: function () {
          alert('Ungültiger oder abgelaufener PIN. Bitte versuchen Sie es erneut.');
        }
      });
    },
    

    _onFooterClick: function (e) {
      if (e.target.classList.contains("cancel-reply")) {
        this._disableActiveReply();
      } else if (e.target.classList.contains("save-reply")) {
        var content = e.currentTarget.querySelector(
          ".reply-textarea-wrapper .reply-textarea"
        ).value;
        // Die E-Mail-Adresse aus dem versteckten Feld abrufen
        var email = e.currentTarget.querySelector(
          ".reply-email-input"
        ).value;
        if (!this._isValidEmail(email)) {
          alert("Bitte geben Sie eine gültige E-Mail-Adresse ein.");
          return;
        }
        this._onReplySave({
          content: content,
          reply_to_id: e.target.dataset.id,
          email: email, // E-Mail hinzufügen
      });
      }
    },
    _onRemoveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_delete",
        {
          id: id,
        },
        function (e) {
            if (ajaxReload) {
                $(".modal").modal("hide");

                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    _onApproveComment: function (e) {
      var id = e.currentTarget.dataset.id;
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_approve",
        {
          id: id,
        },
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    _disableActiveReply: function () {
      $(".comment .reply-textarea-wrapper").remove();
    },
    _onReplyToComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var id = e.currentTarget.dataset.id;
      var comment = $(e.currentTarget).closest(".comment");
      var textarea = $('<textarea rows="5" class="form-control reply-textarea">');
      // Erstelle ein Eingabefeld für die E-Mail-Adresse
      var emailInput = $('<input>', {
        type: 'email',
        placeholder: this._("Deine E-Mail Adresse"),
        class: 'form-control reply-email-input',
      });
      comment.find(".comment-footer").append(
        $('<div class="control-full reply-textarea-wrapper">').append(
          textarea,
          emailInput,
          $("<div>")
            .addClass("reply-actions")
            .append(
              $("<button>", { text: this._("Antworten"), "data-id": id }).addClass(
                "btn btn-default reply-action save-reply"
              ),
              $("<button>", { text: this._("Cancel") }).addClass(
                "btn btn-danger reply-action cancel-reply"
              )
            )
        )
      );
    },
    _disableActiveEdit: function () {
      $(".comment.edit-in-progress")
        .removeClass(".edit-in-progress")
        .find(".comment-action.save-comment")
        .addClass("hidden")
        .prevObject.find(".comment-action.edit-comment")
        .removeClass("hidden")
        .prevObject.find(".edit-textarea-wrapper")
        .remove()
        .prevObject.find(".comment-content")
        .removeClass("hidden");
    },
    _onEditComment: function (e) {
      this._disableActiveReply();
      this._disableActiveEdit();
      var target = $(e.currentTarget).addClass("hidden");
      target.parent().find(".save-comment").removeClass("hidden");
      var content = target
        .closest(".comment")
        .addClass("edit-in-progress")
        .find(".comment-content");
      var textarea = $('<textarea rows="5" class="form-control">');
      textarea.text(content.text());
      content
        .addClass("hidden")
        .parent()
        .append(
          $('<div class="control-full edit-textarea-wrapper">').append(textarea)
        );
    },
    _onSaveComment: function (e) {
      var self = this;
      var id = e.currentTarget.dataset.id;
      var target = $(e.currentTarget);
      var notify = this.sandbox.notify;
      var _ = this.sandbox.translate;
      var content = target.closest(".comment").find(".comment-body textarea");
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_update",
        {
          id: id,
          content: content.val(),
        },
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        },
        function (err) {
          console.log(err);
          var oldEl = notify.el;
          notify.el = target.closest(".comment");
          notify(
            self._("An Error Occurred").fetch(),
            self._("Comment cannot be updated").fetch(),
            "error"
          );
          notify.el.find(".alert .close").attr("data-dismiss", "alert");
          notify.el = oldEl;
        }
      );
    },
    _onSubmit: function (e) {
      e.preventDefault();
      var data = new FormData(e.target);
      this._saveComment({ content: data.get("content"), author_email: data.get("author_email"), guest_user: data.get("guest_user"), create_thread: true });
    },
    _saveComment: function (data) {
      if (!data.content) {
        return;
      }

      data.subject_id = this.options.subjectId;
      data.subject_type = this.options.subjectType;
      var ajaxReload = this.options.ajaxReload;

      this.sandbox.client.call(
        "POST",
        "comments_comment_create",
        data,
        function () {
            if (ajaxReload) {
                $(document).trigger("comments:changed");
            } else {
                window.location.reload();
            }
        }
      );
    },
    // Validiert die E-Mail-Adresse
    _isValidEmail: function (email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    },
  };

});
