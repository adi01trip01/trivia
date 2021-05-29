import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# Function for questions pagination
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    formatted_questions = [question.format() for question in selection]
    current_question = formatted_questions[start:end]
    return current_question


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    # cors = CORS(app, resources={r"*/*": {"origins": "*"}})
    CORS(app, resources={'/': {'origins': '*'}})
    '''
    @TODO: Use the after_request decorator to set Access-Control-Allow
    '''

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET POST PATCH DELETE OPTIONS')
        return response

    '''
    @TODO: 
    Create an endpoint to handle GET requests 
    for all available categories.
    '''

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        current_category = {}
        for c in categories:
            current_category[c.id] = c.type
        return jsonify({
            'categories': current_category,
            'success': True
        })

    '''
    @TODO: 
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 
  
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.all()
        current_category = {}
        for c in categories:
            current_category[c.id] = c.type
        current_question = paginate_questions(request, questions)
        data = {
            'questions': current_question,
            'total_questions': len(Question.query.all()),
            'categories': current_category,
            'success': True
        }
        if len(current_question) == 0:
            abort(404)
        else:
            return jsonify(data)

    '''
    @TODO: 
    Create an endpoint to DELETE question using a question ID. 
  
    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_questions(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())

            })
        except:
            abort(422)

    '''
    @TODO: 
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.
  
    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  
    '''

    @app.route('/questions', methods=['POST'])
    def add_questions():
        body = request.get_json()

        new_question = body.get('question')
        new_answer = body.get('answer')
        if new_question == '':
            new_question = None
        if new_answer == '':
            new_answer = None
        new_category = body.get('category')
        new_difficulty = body.get('difficulty')
        print(new_question, new_answer)
        if (new_question is None) or (new_answer is None):
            abort(422)

        try:

            question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty,
                                category=new_category)
            question.insert()

            questions = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, questions)

            return jsonify({
                'created': question.id,
                'questions': current_questions,
                'total questions': len(Question.query.all()),
                'success': True
            })
        except:
            abort(422)

    '''
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm')

        if search_term:
            search_results = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            return jsonify({
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
                'success': True
            })
        abort(404)

    '''
    @TODO: 
    Create a GET endpoint to get questions based on category. 
  
    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            questions = Question.query.filter(Question.category == str(category_id)).all()

            return jsonify({
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id,
                'success':True
            })
        except:
            abort(404)

    '''
    @TODO: 
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 
  
    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_trivia_game():

        try:
            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            completed_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(Question.id.notin_(completed_questions)).all()
            else:
                available_questions = Question.query.filter_by(category=category['id']). \
                    filter(Question.id.notin_(completed_questions)).all()

            next_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': next_question
            })
        except:
            abort(422)

    '''
    @TODO: 
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 404,
            'message': 'The resource you requested not found',
            'success': False
        }), 404

    @app.errorhandler(422)
    def not_processable(error):
        return jsonify({
            'error': 422,
            'message': 'The request is not processable',
            'success': False
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 400,
            'message': 'This is a bad request',
            'success': False
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'error': 405,
            'message': 'This method is not allowed here',
            'success': False
        }), 405

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'error': 500,
            'message': 'The server encountered an unexpected condition that prevented it from fulfilling the request',
            'success': False
        }), 500
    return app
