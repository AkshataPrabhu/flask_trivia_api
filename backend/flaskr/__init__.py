import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
CATEGORIES_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [q.format() for q in selection]
    current_questions = questions[start:end]

    return current_questions


def paginate_categories(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * CATEGORIES_PER_PAGE
    end = start + CATEGORIES_PER_PAGE
    categories = [c.format() for c in selection]
    current_categories = categories[start:end]
    return current_categories


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories", methods=["GET"])
    def get_all_categories():
        categories = Category.query.all()
        formatted_category = {c.id: c.type for c in categories}
        return jsonify({
            'success': True,
            'categories': formatted_category
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.
   

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions", methods=["GET"])
    def get_questions_pagination():
        questions = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, questions)
        categories = Category.query.all()
        format_categories = {str(c.id): c.type for c in categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(questions),
                "categories": format_categories,
                "current_category": "History"
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_questions_by_id(question_id):
        q = Question.query.get(question_id)
        if q == None:
            abort(404)
        deleted_question = q.delete()
        question_count = len(Question.query.all())
        return jsonify({
            "success": True,
            "total_questions": question_count,
            "deleted": question_id
        })

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=["POST"])
    def create_questions():
        body = request.get_json()
        try:
            answer = body.get("answer", None)
            category = body.get("category", None)
            difficulty = body.get("difficulty", None)
            question = body.get("question")
            q = Question(question=question, category=category, difficulty=difficulty, answer=answer)
            q.insert()

            return jsonify(
                {
                    "success": True,
                    "created": q.id
                }
            )

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/search", methods=["POST"])
    def get_questions_by_search_term():
        body = request.get_json()
        searchTerm = "%" + body.get("searchTerm", None) + "%"

        try:
            q = Question.query.filter(Question.question.ilike(searchTerm)).all()

            current_questions = paginate_questions(request, q)
            questions = [que.format() for que in q]
            return jsonify(
                {
                    "success": True,
                    "questions": questions,
                    "total_questions": len(questions),
                    "current_category": "currentCategory"
                }
            )
        except Exception:
            abort(422)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_for_category(category_id):

        try:
            category = Category.query.get(category_id);
            category_name = category.type
            filtered_questions = Question.query.order_by(Question.id).filter(Question.category == category.id).all()
            questions = [q.format() for q in filtered_questions]
            return jsonify({
                "success": True,
                "questions": questions,
                "total_questions": len(questions),
                "current_category": category_name,
            })

        except Exception:
             abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route("/quizzes", methods=["POST"])
    def get_quiz_questions():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        quiz_category = body.get("quiz_category", None)
        quiz_id = quiz_category["id"]
        filtered_questions = []
        try:
            if quiz_id == 0:
                filtered_questions = Question.query.all()
            else:
                filtered_questions = Question.query.order_by(Question.id).filter(Question.category == quiz_id).all()
            all_question_ids = [i.id for i in filtered_questions]
            #print(all_question_ids)
            #print(previous_questions)
            questions_left = []
            for i in all_question_ids:
                if i not in previous_questions:
                    questions_left.append(i)
            #print("ques left ", questions_left)
            if len(questions_left) == 0:
                return jsonify({
                    "success": True,
                    "question": None
                })
            question_picked_id = random.choice(questions_left)
            question_picked = Question.query.get(question_picked_id).format()
            return jsonify({
                "success": True,
                "question": question_picked
            })
        except Exception:
            abort(422)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    return app
