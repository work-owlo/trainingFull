import openai
import time

openai.api_key = "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"

model_engine = "gpt-3.5-turbo"

def generate_compliance_questions(text):
    # prompt = "Generate a comma seperated list of 10 questions to ask an employee about the following policy"
    # prompt += text
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "user", "content": prompt},
    #     ]
    #     )

    # return completion.choices[0].message
    time.sleep(2)
    return {
        "content": "\n\n1. Can you explain the policy for being paid for all hours worked%s\n2. What should an employee do if there is a discrepancy in their pay or hours worked%s\n3. How are work schedules determined%s \n4. What happens if an employee needs time off after the schedules have been posted%s \n5. How much notice is required for scheduling requests%s \n6. Who should an employee contact for approval of time off, even in an emergency%s \n7. What is the procedure for calling in sick for an opener%s \n8. How much notice is required for calling in sick for all other shifts%s \n9. What happens if an employee is absent without permission or advanced notice%s \n10. What is the importance of an employee's availability and flexibility for their work schedule%s",
        "role": "assistant"
        }


def generate_description(text):
    # prompt = "Generate a 1 sentence description of the following policy"
    # prompt += text
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "user", "content": prompt},
    #     ]
    #     )
    # return completion.choices[0].message['content']
    # time.sleep(2)
    return "This policy outlines the expectations for employee compensation, flexible scheduling, and communication regarding scheduling and time off requests, including guidelines for calling in sick and potential consequences for no call/no show situations"

def format_questions(questions):
    #     {
    # "content": "\n\n1. Can you explain the policy for being paid for all hours worked%s\n2. What should an employee do if there is a discrepancy in their pay or hours worked%s\n3. How are work schedules determined%s \n4. What happens if an employee needs time off after the schedules have been posted%s \n5. How much notice is required for scheduling requests%s \n6. Who should an employee contact for approval of time off, even in an emergency%s \n7. What is the procedure for calling in sick for an opener%s \n8. How much notice is required for calling in sick for all other shifts%s \n9. What happens if an employee is absent without permission or advanced notice%s \n10. What is the importance of an employee's availability and flexibility for their work schedule%s",
    # "role": "assistant"
    # }
    # into a list of questions [<question1>, <question2>, ...]
    # return questions
    questions = questions["content"].split("\n")[1:]
    # trim 
    questions = [q.strip() for q in questions]
    # remove empty strings
    questions = [q for q in questions if q]
    # remove numbers from questions (e.g. "1. Can you explain the policy for being paid for all hours worked%s" -> "Can you explain the policy for being paid for all hours worked%s")
    questions = [q.split(". ", 1)[1] for q in questions]
    return questions


def check_response(context, question, answer):
    # prompt = "Check if the following response is correct. Start respnse with 'Yes' or 'No'.\n"
    # prompt += f"Question: {question}"
    # prompt += f"Answer: {answer}"
    # prompt += f"Context: {context}"
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "user", "content": prompt},
    #     ]
    #     )
    # return completion.choices[0].message['content']
    # # time.sleep(2)
    return "Yes, that is correct"


def generate_simulator(num_chats, customer, situation, problem, respond):
    return  "Hello, I would like to return a damaged item I received."
    # prompt = f"Problem: {problem} "
    # prompt += f"You play the role of a {customer}"
    # prompt += f"Sitation: {situation}"
    # # prompt += f"Respond: {respond}"
    # prompt += f"Make the conversation last {num_chats * 2} chats"
    # prompt += "Only give me the first chat of the conversation"
    # completion = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #     ])
    # return completion.choices[0].message['content']
    # time.sleep(2)
    return "Yes, that is correct"


def generate_simulation_response(init, question_history):
    # add init to question_history as first element
    question_history.insert(0, init)
    # get the latest question
    # question_history[-1]['content'] = question_history[-1]['content'] + "generate reply to this question with you as the customer"
    print(question_history) 
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=question_history

        )
    response = completion.choices[0].message['content']
    # return part after semicolon if it exists
    if ":" in response:
        response = response.split(":")[1]
    return response
    # # time.sleep(2)
    return "Yes, that is correct"