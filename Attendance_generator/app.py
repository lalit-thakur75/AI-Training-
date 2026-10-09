import os,json,ast,operator
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
client=InferenceClient(api_key=os.getenv("HF_TOKEN"))
MODEL="Qwen/Qwen2.5-72B-Instruct"
FILE=Path(__file__).parent/"attendance.json"

def data():
    return json.loads(FILE.read_text())

def save(d):
    FILE.write_text(json.dumps(d,indent=2))

def attendance(action,name=None,present=None,total=None):
    d=data()["students"]

    if action=="all":
        return d

    if action in ("student","percentage"):
        s=next((x for x in d if x["student_name"].lower()==name.lower()),None)
        if not s:return {"error":f"Student '{name}' not found"}
        return {**s,"attendance_percentage":round(s["days_present"]/s["total_days"]*100,2)}

    if action in ("highest","lowest"):
        r=[{**s,"attendance_percentage":round(s["days_present"]/s["total_days"]*100,2)} for s in d]
        return max(r,key=lambda x:x["attendance_percentage"]) if action=="highest" else min(r,key=lambda x:x["attendance_percentage"])

    if action=="update":
        s=next((x for x in d if x["student_name"].lower()==name.lower()),None)
        if not s:return {"error":f"Student '{name}' not found"}
        if present<0 or total<=0 or present>total:return {"error":"Invalid attendance values"}
        s["days_present"],s["total_days"]=present,total
        save({"students":d})
        return {**s,"attendance_percentage":round(present/total*100,2)}

    return {"error":"Invalid attendance action"}

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Mod:operator.mod,ast.Pow:operator.pow,ast.USub:operator.neg}

def calc(expr):
    def ev(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
        if isinstance(n,ast.BinOp):return OPS[type(n.op)](ev(n.left),ev(n.right))
        if isinstance(n,ast.UnaryOp):return OPS[type(n.op)](ev(n.operand))
        raise ValueError("Invalid expression")
    return round(ev(ast.parse(expr,mode="eval").body),4)

SYSTEM="""
You are an AI attendance agent.
Return ONLY valid JSON.
Choose exactly one tool: attendance or calculator.

attendance actions:
all, student, percentage, highest, lowest, update

Example:
{"tool":"attendance","arguments":{"action":"percentage","name":"Rahul"}}

Calculator example:
{"tool":"calculator","arguments":{"expression":"(42/50)*100"}}

Update example:
{"tool":"attendance","arguments":{"action":"update","name":"Rahul","present":45,"total":55}}

Never invent attendance data.
"""

def ai(question):
    r=client.chat_completion(
        model=MODEL,
        messages=[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":question}
        ],
        temperature=0
    )
    return json.loads(r.choices[0].message.content)

def run(question):
    decision=ai(question)
    tool,a=decision["tool"],decision["arguments"]

    if tool=="attendance":
        result=attendance(a["action"],a.get("name"),a.get("present"),a.get("total"))
    elif tool=="calculator":
        result={"result":calc(a["expression"])}
    else:
        result={"error":"Unknown tool"}

    return {
        "query":question,
        "tool_used":tool,
        "tool_arguments":a,
        "result":result
    }

if __name__=="__main__":
    print(json.dumps(run(input("Query: ")),indent=2))
