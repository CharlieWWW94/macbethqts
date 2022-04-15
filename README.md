# macbethqts
A web app that allows users to search my API for quotations from the play Macbeth and also practise these quotations by completing gap fill exercises of varying difficulty (easy, medium, hard). Built using Python, Flask, CSS, HTML, Jinja and Bootstrap.

Try out the app here:

http://macbethqts.herokuapp.com/

The app now supports:
- User registration and logins. User passwords are hashed and salted and stored in a db via SQLAlchemy.
- Performance tracking. Users with accounts' quiz results are saved and their average score is calculated and displayed to them on their dashboard.
- Users can save important quotations that can then be accessed via their dashboard. The dashboard also allows users to complete Quick Learn activities and quizzes based on their custom saved list.
  
