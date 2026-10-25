from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def pick_llm(level: str):
    """
    Picks the appropriate Gemini LLM based on the level of the question.

    Args:
        level (str): The level of the question, can be "low", "medium", or "high".

    Returns:
        ChatGoogleGenerativeAI: The LLM instance to be used.
    """
    if level.lower() == "low":
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    elif level.lower() == "medium":
        # Flash can also be used here, or you can step up to Pro for better reasoning
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
    elif level.lower() == "high":
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
    else:
        raise ValueError(f"Unsupported level: {level}")

    return llm

if __name__ == "__main__":
    llm_obj = pick_llm("low")  
    # .invoke() returns an AIMessage object. .content extracts the text string.
    response = llm_obj.invoke("What is the capital of France?")
    print(response.content)