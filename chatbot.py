import openai

class Chatbot():
    def __init__(self, user_id, training_id, module_id, company_id):
        self.user_id = user_id
        self.training_id = training_id
        self.module_id = module_id
        self.company_id = company_id
        self.context = self.get_context(training_id, module_id, company_id)
        self.state = 1
        self.queries, self.responses = self.get_messages(training_id, module_id, company_id)
        self.progress_tracker = self.get_progress_tracker(training_id, module_id, company_id)


    #Includes the chat api calls, the chatbot, and the verification stuff for the chatbot (loading data from the database for contetxt)
    def get_context(sefl, training_id, module_id, company_id):
        #Get the context from the database for the given module, training, and company.
        #For now just return the mcdonalds context as a string.
        with(open("./text_files/full_data.txt") as file_desc):
            context = file_desc.read()

    def get_messages(self, training_id, module_id, company_id):
        #Get the messages from the database for the given module, training, and company.
        #For now, empty (database not implemented)
        return [(), ()]
    
    def get_progress_tracker(self, training_id, module_id, company_id):
        #Get the progress tracker from the database for the given module, training, and company.
        #For now, empty (database not implemented)
        return []
    
    def respond(self, query):
        #Respond to the query
        try:
            response = openai.Completion.create(
                prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
                temperature=0,
                max_tokens=300,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                model="text-davinci-003",
            )

        except Exception as e:
            print(e)
            response = "Sorry, there was an error. Please ask the question again, maybe in a different way."

        self.queries.append(query)
        self.responses.append(response)
        return response

    
