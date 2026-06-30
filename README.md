# Chatbot


I completed everything with all comments for easier understanding.

To run and test it . 
Default value for login :
Username: alice
Password:secret

Also to run a program follow these steps:
1 Install python and SQL (command for SQL python -m pip install -r requirements.txt or -m pip install sqlalchemy)
2. Run database.py
3.Run a server first . 
4. Create a new terminal
5. Split a terminal in any amount of chat rooms you would like to have 
6. In each chat room insert this command 
cd /workspaces/Final_assigment
python client.py
7. To exit a chat type /quit and press Enter or press Ctrl+C ( I created 2 ways)
8. Running the server in the Docker
# Build the image
docker build -t chat-server .

# Run the container (server inside)
docker run --rm --name chat-server-container -p 5000:5000 chat-server


