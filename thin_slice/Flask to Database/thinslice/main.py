import os
from flask import Flask, send_file, render_template_string
from flask import request
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials

app = Flask(__name__)

# Initialize Firebase ONLY ONCE at the top level
if not firebase_admin._apps:
    # Add your credentials here if needed
    # cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
    # firebase_admin.initialize_app(cred)
    firebase_admin.initialize_app()

db = firestore.client()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body>
    <form action="/process" method="POST">
      <input type="text" name="user_input" placeholder="Enter a Name">
      <button type="submit">Submit</button>
    </form>

    <p>Name: {{ Name }}</p>
    
    <form action="/button-click" method="POST">
      <button type="submit">Click Me for Names</button>
    </form>
  </body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, Name="Waiting for Data")

@app.route("/button-click", methods=['POST'])
def fetch_data():
    # REMOVED: firebase_admin.initialize_app() - Don't initialize again!
    collection_ref = db.collection("People")
    People = collection_ref.stream()
    
    names = []
    for person in People:
        person_data = person.to_dict()
        if "Name" in person_data:
            names.append(person_data["Name"])
    
    # Display all names or just the last one
    if names:
        display_name = ", ".join(names)  # Show all names
        # OR if you only want the last one: display_name = names[-1]
    else:
        display_name = "No names found"
    
    return render_template_string(HTML_TEMPLATE, Name=display_name)

@app.route("/bing.com")  
def bing_route():
    print("this worked")
    with open("myfile.txt", "x") as f:
        pass  # Just create the file
    return send_file('src/index.html')

@app.route('/process', methods=['POST'])
def process_input():
    user_input = request.form['user_input']
    with open("myfile.txt", "a") as f:
        f.write(user_input + "\n")  # Added newline for better formatting

    doc_ref = db.collection("People").document()
    doc_ref.set({"Name": user_input})
    
    # Return the template instead of send_file for consistency
    return render_template_string(HTML_TEMPLATE, Name=f"Added: {user_input}")

def main():
    app.run(port=int(os.environ.get('PORT', 80)), debug=True)

if __name__ == "__main__":
    main()