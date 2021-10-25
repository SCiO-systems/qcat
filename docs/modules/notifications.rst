Notifications
=============

The Django app :mod:`notifications` handles the creation and display of logs for
the review process. These are the most important decisions

Signals
-------
* Signals are used to fire events that mark a change in the workflow
* Classic functions could be used, the decision for signals was made because

  * More receivers are likely to be implemented soon (e.g. auto-assign reviewers)
  * Tasks could be executed asynchronously easily

* All sending signals live in the questionnaire module, notifications receivers
  in the notifications module.

View
----
* Heavily built for asynchronous calls. This is due to heavy queries.
* JS is mostly in the file ``static/notifications/js/notificationActions.js``
* Some logic for the filters depends on the get querystring.

Logic
-----
* Most of the logic is in the ``ActionContextQuerySet``, so it is reusable.
* As content of the mails sent to users needs to be more context-specific (e.g.
  different text when reviewing or publishing or different text when inviting
  editor or reviewer), a split between notifications (as in the notification
  list) and mails (as sent to users after certain actions) was made.

Notifications
-------------
(as in the notification list)

* The text for a notifications subject (the text appearing in the notification
  list) depends on its action and is based on the template
  ``templates/notifications/notification/<action>.html``

Mails
-----
* No mails are sent yet, as the texts and triggers are not stable.
