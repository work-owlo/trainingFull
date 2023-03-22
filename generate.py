import openai
import time
import re
import json

openai.api_key = "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"

model_engine = "gpt-3.5-turbo"

def clean_output(text):
    '''Clean generated output'''
    # get text after first semicolon
    if ":" in text:
        text = text.split(":")[1]

    # remove quotes
    text = text.replace('"', '')
    text = text.replace("'", "")
    # remove any parenthesis and the text inside ex. "hello (one)" is "hello" using regex
    text = re.sub(r'\([^)]*\)', '', text)

    
    return text


def generate_compliance_questions(text):
    prompt = "Generate a comma seperated list of 10 questions to ask an employee about the following policy"
    prompt += text
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
        )

    return completion.choices[0].message
    # time.sleep(2)
    # return {
    #     "content": "\n\n1. Can you explain the policy for being paid for all hours worked?\n2. What should an employee do if there is a discrepancy in their pay or hours worked?\n3. How are work schedules determined? \n4. What happens if an employee needs time off after the schedules have been posted? \n5. How much notice is required for scheduling requests? \n6. Who should an employee contact for approval of time off, even in an emergency? \n7. What is the procedure for calling in sick for an opener? \n8. How much notice is required for calling in sick for all other shifts?\n9. What happens if an employee is absent without permission or advanced notice? \n10. What is the importance of an employee's availability and flexibility for their work schedule?",
    #     "role": "assistant"
        # }


def generate_description(text):
    prompt = "Generate a 1 phrase description of the following policy maximum 20 words"
    prompt += text
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
        )
    return clean_output(completion.choices[0].message['content'])
    # time.sleep(2)
    # return "Expectations for employee compensation, flexible scheduling, and communication regarding scheduling and time off requests"


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
    prompt = "Check if the following response is correct. Start respnse with 'Yes' or 'No'. If correct, give an affermative phrase. If incorrect, say 'No, the correct answer is' and provide correct answer\n"
    prompt += f"Question: {question}"
    prompt += f"Answer: {answer}"
    prompt += f"Context: {context}"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
        )
    answer = clean_output(completion.choices[0].message['content'])
    return answer
    # # time.sleep(2)
    return "Yes, that is correct"


def generate_simulator(num_chats, customer, situation, problem, respond):
    # return  "Hello, I would like to return a damaged item I received."
    prompt = f"Problem: {problem} "
    prompt += f"You play the role of a {customer}"
    prompt += f"Sitation: {situation}"
    # prompt += f"Respond: {respond}"
    prompt += f"Make the conversation last {num_chats * 2} chats"
    prompt += "Only give me the first chat of the conversation"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ])
    return clean_output(completion.choices[0].message['content'])
    # time.sleep(2)
    return "Yes, that is correct"


def generate_simulation_response(init, question_history, tool_name):
    # add init to question_history as first element
    character = "customer" if "customer" in tool_name else "co-worker"
    question_history = question_history[0:]
    question_history.insert(0, init)
    # get the latest question
    question_history[-1]['content'] = question_history[-1]['content'] + ". Generate reply to this question with you as the customer only.  I will answer as the customer service representative"
    # print(question_history) 
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=question_history

        )
    response = completion.choices[0].message['content']
    print(response)
    return clean_output(response)
    # # # time.sleep(2)
    # return "Yes, that is correct"


def generate_steps(task, focus, role, documentation=None):
    '''Generate a list of tasks using openai'''
    prompt = "Generate a list of comprehensive instructions to thoroughly, properly, and safely complete the following task. Each step should be atleast 2 sentences"
    prompt += f"Task: {task} with a focus on {focus} for the role of {role} "
    if documentation:
        prompt += f"Documentation: {documentation[:205]}"
    prompt += "Also generate a list of 12 comprehensive questions I can ask an employee to test their understanding of the task."
    prompt += 'Return as a list of steps in a json {"data": {"steps": [...], "questions": [...]} }, and no other text'
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
        )
    # print(completion)
    value = completion.choices[0].message['content']
    # value = "\n\n{\n  \"data\": {\n    \"steps\": [\n      \"Begin by assessing the weight and dimensions of the box(es) before attempting to lift them. Always ensure that the boxes can be lifted safely and without risk of injury.\",\n      \"Take a moment to stretch and loosen up your muscles, especially your back and legs, before lifting. Stand in front of the box with your feet shoulder-width apart.\",\n      \"Squat down, bending at the knees, and grip the box firmly with both hands. Keep your back straight and lift the box up slowly, using the force from your legs rather than your back.\",\n      \"Once the box is off the ground, hug it close to your body to maintain balance and control. Avoid twisting your body or jerking the box in any direction.\",\n      \"If necessary, take small steps to move the box to its desired location. Avoid sudden movements and be aware of your surroundings at all times.\",\n      \"If you need to lift multiple boxes, take breaks as needed to avoid overexertion and fatigue. Always prioritize safety over speed.\",\n      \"When you're finished lifting, take a few additional moments to stretch and relax your muscles. Avoid any activities that could put additional strain on your back or joints.\",\n      \"If you experience discomfort or pain while lifting, stop immediately and seek medical attention if necessary. Report any accidents or injuries to your supervisor.\",\n      \"Be aware of any safety equipment or procedures provided by your employer, such as back braces or lifting devices. Use them as directed to minimize the risk of injury.\",\n      \"Maintain proper posture throughout the lifting process. Keep your shoulders back, your chest out, and your head looking forward.\",\n      \"Take the necessary precautions to prevent slips and falls, especially if you're lifting boxes in a wet or slippery environment. Wear slip-resistant shoes and be mindful of any hazards in your surroundings.\",\n      \"Communicate with your coworkers and supervisors to ensure that everyone is on the same page regarding safety procedures and expectations.\",\n    ],\n    \"questions\": [\n      \"What should you do before attempting to lift a heavy box?\",\n      \"Which part of your body should you prioritize when stretching before lifting?\",\n      \"How should you grip a heavy box when lifting it up?\",\n      \"What should you do to maintain balance and control when lifting a heavy box?\",\n      \"How should you move a heavy box from one location to another?\",\n      \"What should you do if you need to lift multiple heavy boxes?\",\n      \"Why should you prioritize safety over speed when lifting heavy boxes?\",\n      \"What should you do if you experience discomfort or pain while lifting?\",\n      \"What safety equipment or procedures might be provided by your employer to help you lift heavy boxes safely?\",\n      \"What is the proper posture for lifting a heavy box?\",\n      \"What precautions should you take to prevent slips and falls when lifting heavy boxes?\",\n      \"Why is communication important for lifting heavy boxes safely?\",\n    ]\n  }\n}"
    # remove all \n
    value = value.replace("\n", "")
    # remove all \t
    value = value.replace("\t", "")
    # remove all \ 
    value = value.replace("\\", "")
    print(value)
    # remove any space between , and ] using regex
    value = re.sub(r',\s*]', ']', value)
    # replace all ,] with ]
    value = value.replace(",]", "]")

    return json.loads(value)["data"]


def generate_physical_questions(task, focus, role, documentation=None):
    prompt = "Generate a list of 12 comprehensive questions I can ask an employee to test their understanding of the task."
    prompt += f"Task: {task} with a focus on {focus} for the role of {role} "
    if documentation:
        prompt += f"Documentation: {documentation[:205]}"
    prompt += 'Return as a list of steps in a json {"data": ["q1", "q2", ...]}, and no other text'

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt},
        ]
        )
    return clean_output(completion.choices[0].message['content'])

