import uvicorn 



if __name__ == "__main__":
    uvicorn.run("API:app", port=8001, host="127.0.0.1", reload=True)
