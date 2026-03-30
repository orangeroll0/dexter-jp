from fastapi import FastAPI
from dexter_jp.agent import DexterJP # 日本株特化クラス
import uvicorn

app = FastAPI()
agent = DexterJP()

@app.get("/analyze_jp")
async def analyze_jp(query: str):
    # 例: "7203(トヨタ)の直近決算と中期経営計画から、成長性を検証して"
    # dexter-jp は内部でEDINET等を自律検索します
    result = agent.run(query)
    return {"analysis": result}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
