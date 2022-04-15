import copy
import json
import sqlalchemy.exc
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import SubmitField, SelectField
import os
import api_communicator
import random
import ast
import quote_manipulator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQL_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_BINDS"] = {
    "savedquotations": "sqlite:///savedquotations.db"
}

db = SQLAlchemy(app)
Bootstrap(app)


class SearchForm(FlaskForm):
    theme = SelectField('Theme', choices=['All', 'Ambition', 'Bravery', 'Witchcraft', 'Equivocation'])
    character = SelectField('Character', choices=['All', 'Macbeth', 'Lady Macbeth', 'First Witch', 'Captain'])
    act = SelectField('Act', choices=['All', 1, 2])
    scene = SelectField('Scene', choices=['All', 1, 2, 3, 4, 5])
    submit = SubmitField('Submit')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    qf_attempts = db.Column(db.Integer)
    qf_avg = db.Column(db.Integer)
    qf_most_recent = db.Column(db.Integer)
    q_attempts = db.Column(db.Integer)
    q_avg = db.Column(db.Integer)
    q_most_recent = db.Column(db.Integer)


class SavedQuotations(db.Model):
    __bind_key__ = "savedquotations"
    id = db.Column(db.Integer, primary_key=True)
    db_q_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)


db.create_all()
db.session.commit()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    if User.query.get(user_id) is None:
        return
    else:
        return User.query.get(user_id)


@app.route("/", methods=["GET", "POST"])
def home():
    form = SearchForm()
    if form.validate_on_submit():
        list_search_params = list(form.data.items())
        test = api_communicator.search(list_search_params)
        if type(test) == str:
            return test
        else:
            session['quotations'] = test['quotations']
            return display_results(test)

    return render_template("index.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        reg_details = request.values.to_dict()
        reg_username = reg_details["username"]
        hashed_reg_password = generate_password_hash(password=reg_details["password"], method='pbkdf2:sha256',
                                                     salt_length=8)

        new_user = User(username=reg_username, password=hashed_reg_password)
        try:
            db.session.add(new_user)
            db.session.commit()

        except sqlalchemy.exc.IntegrityError:
            error = "This username is already in use, please try another."
            return render_template("register.html", error=error)
        return render_template("login.html", invitation="Please sign in to your new account!")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_details = request.values.to_dict()
        given_username = login_details['username']
        given_password = login_details['password']
        user_to_login = User.query.filter_by(username=given_username).first()

        if user_to_login and check_password_hash(pwhash=user_to_login.password, password=given_password):
            login_user(user_to_login)
            return redirect(url_for('load_dashboard'))
        else:
            error = "The details provided did not match our database. Please try again."
            return render_template("login.html", error=error)

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete")
def delete_account():
    User.query.filter_by(username=current_user.username).delete()
    SavedQuotations.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for('logout'))


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def load_dashboard():
    form = SearchForm()
    if request.method == "POST":
        if "to_remove" in request.args.to_dict():
            id_to_remove = request.args.to_dict()['to_remove']
            quote_to_remove = SavedQuotations.query.filter_by(db_q_id=id_to_remove, user_id=current_user.id).first()
            db.session.delete(quote_to_remove)
            db.session.commit()
            return redirect(url_for("load_dashboard"))

        elif form.validate_on_submit():
            list_search_params = list(form.data.items())
            test = api_communicator.search(list_search_params)
            session['quotations'] = test['quotations']
            return display_results(test)

    user = User.query.filter_by(username=current_user.username).first()
    user_q_average = user.q_avg

    saved_quotations = SavedQuotations.query.filter_by(user_id=current_user.id).all()
    saved_quotation_ids = [int(ident.db_q_id) for ident in saved_quotations]
    api_response_sq = {'quotations': []}

    if len(saved_quotation_ids) != 0:
        api_response_sq = api_communicator.search(saved_quotation_ids)
        session['quotations'] = api_response_sq["quotations"]

    if user_q_average is not None:
        pb_calc = lambda x: 25 * round(x / 25)
        user_pb_q_average = pb_calc(user.q_avg)
        user_pb_recent = pb_calc(user.q_most_recent)
    else:
        user_pb_q_average = 0
        user_pb_recent = 0

    return render_template("dashboard.html", form=form, user=user, pb_average=user_pb_q_average,
                           pb_recent=user_pb_recent, dash_qts=api_response_sq)


@app.route("/search_results/<results>", methods=["GET", "POST"])
def display_results(results):
    if request.method == "POST":
        save_request = request.values.to_dict()
        if 'id' in save_request:
            saved_q_query = SavedQuotations.query.filter_by(db_q_id=save_request['id']).all()
            duplicate_check = [saved_q for saved_q in saved_q_query if saved_q.user_id == current_user.id]

            if len(duplicate_check) == 0:
                new_quotation = SavedQuotations(db_q_id=save_request['id'], user_id=current_user.id)
                db.session.add(new_quotation)
                db.session.commit()
                return render_template("search_results.html", results=ast.literal_eval(str(results)), saved=1)

            else:
                return render_template("search_results.html", results=ast.literal_eval(str(results)), saved=2)

        return render_template("search_results.html", results=ast.literal_eval(str(results)))


@app.route("/quick_learn/<target_quotation>", methods=["GET", "POST"])
def quick_learn(target_quotation, attempt_tally=1):
    if request.method == "POST":
        quick_request_info = request.values.to_dict()
        new_tally = int(quick_request_info['attempt_tally'])
        if new_tally == 2:
            session["ql_score"] = 0
        elif new_tally == 25:
            return redirect(url_for("quick_learn_result", target_quotation=target_quotation))

        # This is the complete quotation to verify answer again. Type: list
        qf_dict_list = ast.literal_eval(target_quotation)
        if type(qf_dict_list) != list:
            qf_dict_list = [ast.literal_eval(target_quotation)]

        # This is the quotation with Xs in it to replace with the submission
        qf_to_complete = ast.literal_eval(quick_request_info['old_target'])

        # This fills the gaps and then checks if the user submitted answer is correct.
        gap_to_fill = qf_to_complete['quotations'][0]['quotation'].index('X')
        qf_to_complete['quotations'][0]['quotation'][gap_to_fill] = quick_request_info[str("gap")]

        if qf_to_complete['quotations'][0] == qf_dict_list[0]:
            answer_result = 2
            if "ql_score" in session:
                session["ql_score"] += 1
            else:
                session["ql_score"] = 1
        else:
            answer_result = 1
        quick_quotation_new = quote_manipulator.create_gaps(qf_dict_list, difficulty='easy')
        return render_template("quick_learn.html", quotation=quick_quotation_new, attempt_tally=int(new_tally),
                               original_quotation=qf_dict_list, answer_result=answer_result)

    quick_quotation_list = [ast.literal_eval(target_quotation)]
    quick_quotation = quote_manipulator.create_gaps(quick_quotation_list, difficulty='easy')

    return render_template("quick_learn.html", quotation=quick_quotation, attempt_tally=attempt_tally,
                           original_quotation=quick_quotation_list)


@app.route("/quick_learn_result", methods=["GET", "POST"])
def quick_learn_result():
    target_quotation = request.values.to_dict()["target_quotation"]
    total_ql_score = session["ql_score"]
    ql_score_pb = quote_manipulator.progress_bar_percent(total_ql_score) * 4
    return render_template("quick_learn_results.html",
                           bar_percentage=ql_score_pb,
                           score=total_ql_score,
                           attempted_q=target_quotation)


@app.route("/select_difficulty")
def select_difficulty():
    return render_template("select_difficulty.html")


@app.route("/learn_quotations/<difficulty>", methods=["GET", "POST"])
def learn_quotations(difficulty):
    quotations_to_learn = session.get('quotations', None)
    quotations_to_complete = quote_manipulator.create_gaps(quotations_to_learn, difficulty=difficulty)

    # This section of code processes the result

    if request.method == 'POST':
        request_info = request.values.to_dict()
        quotations_from_page = ast.literal_eval(request_info['quotations'])


        index = 0
        for entry in quotations_from_page['quotations']:
            # index = quotations_from_page['quotations'].index(entry)
            for num in range(0, entry['quotation'].count('X')):
                gap_to_fill = entry['quotation'].index('X')
                entry['quotation'][gap_to_fill] = request_info[str(index)]
                index += 1

        return redirect(url_for("quiz_results", submitted_answers=quotations_from_page["quotations"],
                                quotations_to_learn=quotations_to_learn, difficulty=difficulty))

    return render_template("learn_quotations.html", difficulty=difficulty, quotations=quotations_to_complete, space=" ")


@app.route("/quiz_results/<submitted_answers>/<quotations_to_learn>/<difficulty>", methods=["GET", "POST"])
def quiz_results(submitted_answers, quotations_to_learn, difficulty):
    submitted_answers_list = ast.literal_eval(submitted_answers)
    quotations_to_learn_list = ast.literal_eval(quotations_to_learn)

    if type(submitted_answers_list) != list:
        submitted_answers_list = [submitted_answers_list]
        quotations_to_learn_list = [quotations_to_learn_list]

    for entry in submitted_answers_list:
        entry_index = submitted_answers_list.index(entry)
        if entry == quotations_to_learn_list[entry_index]:
            entry['quotation'] = " ".join(entry['quotation'])
            entry['correct'] = 1
        else:
            entry['correct'] = 0
            entry_location = submitted_answers_list.index(entry)
            entry['correct_answer'] = " ".join(quotations_to_learn_list[entry_location]['quotation'])
            entry['quotation'] = " ".join(entry['quotation'])

    percentage_score = round(quote_manipulator.quiz_percentage(submitted_answers_list))
    # rounds percentage score to 25 for bootstrap progress bar:
    pb_calc = lambda x: 25 * round(x / 25)

    # processes of this type should probably go in a separate module... >>>
    if current_user.is_authenticated:

        user_to_update = User.query.filter_by(username=current_user.username).first()
        user_to_update.q_most_recent = percentage_score

        if user_to_update.q_attempts is not None:
            user_to_update.q_attempts += 1
        else:
            user_to_update.q_attempts = 1

        running_avg = quote_manipulator.overall_percentage(attempt_numbers=user_to_update.q_attempts,
                                                           new_avg=percentage_score,
                                                           running_avg=user_to_update.q_avg)
        user_to_update.q_avg = running_avg
        db.session.commit()

    return render_template("quiz_results.html", answers=submitted_answers_list, to_learn=quotations_to_learn,
                           difficulty=difficulty, percentage=percentage_score, pb=pb_calc(percentage_score))


if __name__ == "__main__":
    app.run()
