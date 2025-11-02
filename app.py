import os
from agno.db.sqlite import SqliteDb
from pathlib import Path
from agno.agent import Agent
from agno.media import File
from agno.models.google import Gemini

db = SqliteDb(db_file="chat_history.db")

os.environ["GOOGLE_API_KEY"] = "AIzaSyCE7Rcv1DI8kVPzs2momYdLtRv_9vO5ybU"


uploaded_filename = list(uploaded.keys())[0]
pdf_path = Path(uploaded_filename)


agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    markdown=True,
    add_history_to_context=True, # remembers past messages
    db=db
)

print("You can now chat with the AI. Type 'exit' to quit.")


file_summarized = False

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Ending conversation.")
        break

    if not file_summarized:
        # First input: summarize PDF
        response = agent.run(
            input="Summarize the contents of this PDF file.\n" + user_input,
            files=[File(filepath=pdf_path)]
        )
        file_summarized = True
    else:
        # Subsequent inputs: normal chat without file
        response = agent.run(
            input=user_input
        )

    print("AI:", response.content)
