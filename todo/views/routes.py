from flask import Blueprint, jsonify, request 
from todo.models import db 
from todo.models.todo import Todo 
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET']) 
def get_todos(): 
   args = request.args
   todos = Todo.query.all() 
   result = [] 
   for todo in todos:
      include_todo = True

      # filter by whether tasks are done
      if "completed" in args.keys():
         #should be outside of loop but can't be assed
         if args.get('completed') not in ['true', 'false']:
            return {'error':'completed value not valid. use either "true" or "false"'}, 400
         include_todo = include_todo and (args.get("completed").lower() == str(todo.completed).lower())
      
      # window checks due more than n days away
      if "window" in args.keys():
         current = datetime.now()
         mindelta = timedelta(days=int(args.get('window')))
         include_todo = include_todo and (todo.deadline_at - current <= mindelta)

      if include_todo:
         result.append(todo.to_dict()) 
   return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Return the details of a todo item"""
    todo = Todo.query.get(todo_id) 
    if todo is None: 
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST']) 
def create_todo(): 
   todo = Todo( 
      title=request.json.get('title'), 
      description=request.json.get('description'), 
      completed=request.json.get('completed', False), 
   )

   if todo.title == None:
      return {'error': 'Todo Title must be non-null'}, 400
   if len([a for a in request.json.keys() if a not in todo.to_dict().keys()]) > 0:
      return {'error': 'Extra request fields not accepted'}, 400

   if 'deadline_at' in request.json: 
      todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at')) 
 
   # Adds a new record to the database or will update an existing record 
   db.session.add(todo) 
   # Commits the changes to the database, this must be called for the changes to be saved 
   db.session.commit() 
   return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT']) 
def update_todo(todo_id): 
   todo = Todo.query.get(todo_id) 
   if todo is None: 
      return jsonify({'error': 'Todo not found'}), 404 
   if len([a for a in request.json.keys() if a not in todo.to_dict().keys()]) > 0:
      return {'error': 'Extra request fields not accepted'}, 400
   if request.json.get('id', todo.id) != todo.id:
      return {'error': 'ID field cannot be manually changed'}, 400

   todo.title = request.json.get('title', todo.title) 
   todo.description = request.json.get('description', todo.description) 
   todo.completed = request.json.get('completed', todo.completed) 
   todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
   db.session.commit() 
 
   return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE']) 
def delete_todo(todo_id): 
   todo = Todo.query.get(todo_id) 
   if todo is None: 
      return jsonify({}), 200 
 
   db.session.delete(todo) 
   db.session.commit() 
   return jsonify(todo.to_dict()), 200
 
